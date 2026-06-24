"""
Human review queue service.

Routes uncertain, flagged, or boundary-score submissions to a persistent
queue that teachers can review and override.

v2.1: Added in-memory fallback when PostgreSQL is unavailable.
         This ensures the review queue always works regardless of DB state.

Trigger conditions:
- LLM verdict is UNCERTAIN
- flag_score > 0.7  (integrity concern)
- Final score within 5 points of a grade boundary (25, 50, 75)
- Final score < 10 (likely evaluation failure)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.core.services.database import get_db


# ---------------------------------------------------------------------------
# In-memory fallback store (used when PostgreSQL is unavailable)
# ---------------------------------------------------------------------------

_MEMORY_QUEUE: Dict[str, Dict] = {}


# ---------------------------------------------------------------------------
# Trigger logic
# ---------------------------------------------------------------------------

GRADE_BOUNDARIES = [25, 50, 75]  # Configurable grade boundaries
BOUNDARY_MARGIN = 5              # Points within boundary to trigger review


def _should_queue(result: Dict[str, Any]) -> List[str]:
    """
    Determine if a submission should be queued for review.

    Returns:
        List of trigger reasons (empty if no review needed).
    """
    triggers = []

    # Trigger 1: LLM was uncertain
    llm_verdict = result.get("llm_verdict", "")
    if llm_verdict == "UNCERTAIN":
        triggers.append("UNCERTAIN")

    # Trigger 2: Integrity flag
    flag_score = result.get("flag_score", 0)
    if flag_score > 0.7:
        triggers.append("FLAG")

    # Trigger 3: Score near grade boundary
    final_score = result.get("final_score", 0)
    for boundary in GRADE_BOUNDARIES:
        if abs(final_score - boundary) < BOUNDARY_MARGIN:
            triggers.append("BOUNDARY")
            break

    # Trigger 4: Suspiciously low score (likely evaluation failure)
    if final_score < 10:
        triggers.append("LOW_SCORE")

    # Trigger 5: Integrity flag_reasons exist even if flag_score is low
    flag_reasons = result.get("flag_reasons", [])
    if flag_reasons and len(flag_reasons) > 0 and "FLAG" not in triggers:
        triggers.append("FLAG")

    return triggers


# ---------------------------------------------------------------------------
# Queue operations
# ---------------------------------------------------------------------------

def maybe_queue_for_review(
    submission_id: str,
    student_id: str,
    assignment_id: str,
    result: Dict[str, Any],
) -> Optional[str]:
    """
    Check if submission should be reviewed and insert if so.

    Args:
        submission_id: Unique submission identifier.
        student_id: Student identifier.
        assignment_id: Assignment identifier.
        result: Full evaluation result dict.

    Returns:
        The review queue entry ID if queued, None otherwise.
    """
    triggers = _should_queue(result)
    if not triggers:
        return None

    flag_reasons = result.get("flag_reasons", [])
    if isinstance(flag_reasons, list):
        flag_reasons_json = json.dumps(flag_reasons)
    else:
        flag_reasons_json = json.dumps([])

    # Try database first
    db = get_db()
    if db.available:
        try:
            row = db.execute_one(
                """
                INSERT INTO review_queue
                    (submission_id, student_id, assignment_id, trigger, auto_score, flag_reasons)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                [
                    submission_id,
                    student_id,
                    assignment_id,
                    triggers[0],  # Primary trigger
                    result.get("final_score", 0),
                    flag_reasons_json,
                ],
            )
            return str(row["id"]) if row else None
        except Exception as e:
            print(f"DB review insert failed, falling back to memory: {e}")

    # Fallback: in-memory queue
    review_id = str(uuid.uuid4())
    _MEMORY_QUEUE[review_id] = {
        "id": review_id,
        "submission_id": submission_id,
        "student_id": student_id,
        "assignment_id": assignment_id,
        "trigger": triggers[0],
        "auto_score": result.get("final_score", 0),
        "flag_reasons": json.loads(flag_reasons_json),
        "status": "pending",
        "teacher_score": None,
        "teacher_notes": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return review_id


def get_pending_reviews(
    assignment_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    """Get pending review items, optionally filtered by assignment."""
    # Try database first
    db = get_db()
    if db.available:
        try:
            if assignment_id:
                rows = db.execute(
                    """
                    SELECT * FROM review_queue
                    WHERE status = 'pending' AND assignment_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    [assignment_id, limit],
                )
            else:
                rows = db.execute(
                    """
                    SELECT * FROM review_queue
                    WHERE status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    [limit],
                )
            if rows:
                return _serialize_rows(rows)
        except Exception as e:
            print(f"DB review fetch failed, falling back to memory: {e}")

    # Fallback: in-memory queue
    pending = [
        r for r in _MEMORY_QUEUE.values()
        if r["status"] == "pending"
        and (assignment_id is None or r["assignment_id"] == assignment_id)
    ]
    # Sort by created_at descending
    pending.sort(key=lambda r: r["created_at"], reverse=True)
    return pending[:limit]


def get_review_by_id(review_id: str) -> Optional[Dict]:
    """Get a single review item by ID."""
    # Try database first
    db = get_db()
    if db.available:
        try:
            row = db.execute_one(
                "SELECT * FROM review_queue WHERE id = %s",
                [review_id],
            )
            if row:
                return _serialize_row(row)
        except Exception:
            pass

    # Fallback: in-memory
    return _MEMORY_QUEUE.get(review_id)


def set_teacher_override(
    review_id: str,
    teacher_score: float,
    teacher_notes: str = "",
) -> Optional[Dict]:
    """
    Teacher overrides the auto-generated score.

    The original auto_score is preserved for tracking system accuracy.
    Also propagates the new score to:
    - student_scores table (student profile / history)
    - evaluation_results table (results dashboard)
    """
    # Try database first
    db = get_db()
    if db.available:
        try:
            row = db.execute_one(
                """
                UPDATE review_queue
                SET status = 'reviewed',
                    teacher_score = %s,
                    teacher_notes = %s
                WHERE id = %s
                RETURNING *
                """,
                [teacher_score, teacher_notes, review_id],
            )
            if row:
                serialized = _serialize_row(row)
                # ── Propagate score to student profile ──
                _sync_score_to_student_profile(db, serialized, teacher_score)
                # ── Propagate score to evaluation results ──
                _sync_score_to_evaluation_results(db, serialized, teacher_score)
                return serialized
        except Exception as e:
            print(f"Review override DB error: {e}")

    # Fallback: in-memory
    if review_id in _MEMORY_QUEUE:
        _MEMORY_QUEUE[review_id]["status"] = "reviewed"
        _MEMORY_QUEUE[review_id]["teacher_score"] = teacher_score
        _MEMORY_QUEUE[review_id]["teacher_notes"] = teacher_notes
        return _MEMORY_QUEUE[review_id]
    return None


def _sync_score_to_student_profile(db, review_row: Dict, new_score: float):
    """Update the most recent student_scores entry to reflect teacher override."""
    student_id = review_row.get("student_id", "")
    assignment_id = review_row.get("assignment_id", "")
    if not student_id or not assignment_id:
        return

    try:
        # Update the latest score for this student + assignment combo
        db.execute(
            """
            UPDATE student_scores
            SET score = %s
            WHERE id = (
                SELECT id FROM student_scores
                WHERE student_id = %s AND assignment_id = %s
                ORDER BY submitted_at DESC
                LIMIT 1
            )
            """,
            [new_score, student_id, assignment_id],
        )
        print(f"✓ Student profile synced: {student_id} → {new_score}")
    except Exception as e:
        print(f"⚠ Student profile sync failed (non-fatal): {e}")


def _sync_score_to_evaluation_results(db, review_row: Dict, new_score: float):
    """Update evaluation_results to reflect teacher override."""
    student_id = review_row.get("student_id", "")
    submission_id = review_row.get("submission_id", "")
    if not student_id:
        return

    try:
        # The submission_id in review_queue is "{student_id}_{assignment_id}"
        # but in evaluation_results, submission_id is the student name.
        # Try matching by student_id directly.
        percentage = round(new_score / 100 * 100, 2)  # score is already 0-100
        db.execute(
            """
            UPDATE evaluation_results
            SET final_score = %s,
                percentage = %s
            WHERE id = (
                SELECT id FROM evaluation_results
                WHERE submission_id = %s
                ORDER BY evaluated_at DESC
                LIMIT 1
            )
            """,
            [new_score, percentage, student_id],
        )
        print(f"✓ Evaluation results synced: {student_id} → {new_score}")
    except Exception as e:
        print(f"⚠ Evaluation results sync failed (non-fatal): {e}")


def get_queue_stats() -> Dict:
    """Summary statistics for the review queue."""
    # Try database first
    db = get_db()
    if db.available:
        try:
            row = db.execute_one(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending')  AS pending,
                    COUNT(*) FILTER (WHERE status = 'reviewed') AS reviewed,
                    COUNT(*) AS total,
                    AVG(ABS(auto_score - teacher_score))
                        FILTER (WHERE teacher_score IS NOT NULL) AS avg_override_delta
                FROM review_queue
                """,
            )
            if row:
                return {
                    "available": True,
                    "pending": row["pending"] if row else 0,
                    "reviewed": row["reviewed"] if row else 0,
                    "total": row["total"] if row else 0,
                    "avg_override_delta": round(float(row["avg_override_delta"]), 2)
                        if row and row["avg_override_delta"] is not None else None,
                }
        except Exception:
            pass

    # Fallback: in-memory stats
    all_items = list(_MEMORY_QUEUE.values())
    pending = sum(1 for r in all_items if r["status"] == "pending")
    reviewed = sum(1 for r in all_items if r["status"] == "reviewed")
    return {
        "available": True,
        "source": "in-memory",
        "pending": pending,
        "reviewed": reviewed,
        "total": len(all_items),
        "avg_override_delta": None,
    }


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_row(row: Dict) -> Dict:
    """Convert a DB row to a JSON-safe dict."""
    if not row:
        return {}
    result = dict(row)
    # Convert UUID to string
    for key in ["id"]:
        if key in result and result[key] is not None:
            result[key] = str(result[key])
    # Convert datetime
    for key in ["created_at"]:
        if key in result and result[key] is not None:
            result[key] = result[key].isoformat()
    # Parse flag_reasons if stored as JSON string
    if "flag_reasons" in result and isinstance(result["flag_reasons"], str):
        try:
            result["flag_reasons"] = json.loads(result["flag_reasons"])
        except (json.JSONDecodeError, TypeError):
            result["flag_reasons"] = []
    return result


def _serialize_rows(rows: List[Dict]) -> List[Dict]:
    return [_serialize_row(r) for r in rows]
