"""
Student portal API routes.

All endpoints are scoped to the authenticated student's own data.
Students cannot access other students' information.
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.app.middleware.auth import require_student, TokenPayload
from backend.core.services.database import get_db
from backend.core.services.student_tracker import (
    get_score_history,
    get_improvement_delta,
    get_skill_breakdown,
    get_class_percentile,
    get_student_summary,
)


router = APIRouter(prefix="/api/portal", tags=["student-portal"])


# ---------------------------------------------------------------------------
# ID Resolver — handles the _Result suffix in the database
# ---------------------------------------------------------------------------

def _resolve_db_student_id(login_id: str) -> str:
    """
    Resolve a login username to the actual student_id stored in DB.

    The evaluation pipeline stores IDs like 'student_ravi_Result' or
    '23bds031_Result'. This function checks the DB and returns the
    matching ID, trying multiple patterns.
    """
    db = get_db()
    if not db.available:
        return login_id

    # Try exact match first
    row = db.execute_one(
        "SELECT student_id FROM student_scores WHERE student_id = %s LIMIT 1",
        [login_id],
    )
    if row:
        return row["student_id"]

    # Try with _Result suffix
    suffixed = f"{login_id}_Result"
    row = db.execute_one(
        "SELECT student_id FROM student_scores WHERE student_id = %s LIMIT 1",
        [suffixed],
    )
    if row:
        return row["student_id"]

    # Try LIKE match (e.g. login_id is a prefix)
    row = db.execute_one(
        "SELECT student_id FROM student_scores WHERE student_id LIKE %s LIMIT 1",
        [f"{login_id}%"],
    )
    if row:
        return row["student_id"]

    return login_id


def _get_all_db_ids(login_id: str) -> List[str]:
    """Return all possible DB IDs for this login (for multi-table queries)."""
    resolved = _resolve_db_student_id(login_id)
    ids = {login_id, resolved}
    ids.add(f"{login_id}_Result")
    return list(ids)


def _is_own_id(db_student_id: str, login_id: str) -> bool:
    """Check if a DB student_id belongs to the logged-in user."""
    return (
        db_student_id == login_id
        or db_student_id == f"{login_id}_Result"
        or db_student_id.startswith(login_id)
    )


# ---------------------------------------------------------------------------
# Dashboard — student's own overview
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def student_dashboard(user: TokenPayload = Depends(require_student)):
    """Student's personal dashboard."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    db_id = _resolve_db_student_id(login_id)

    history = get_score_history(db_id, limit=20)
    summary = get_student_summary(db_id)
    class_rank = get_class_percentile(db_id)
    skills = get_skill_breakdown(db_id)

    if history:
        latest_score = history[0]["score"]
        latest_topic = history[0].get("topic_tag", "")
        improvement = get_improvement_delta(
            db_id, topic_tag=latest_topic, current_score=latest_score
        )
    else:
        improvement = {"delta": None, "trend": "no data", "prev_avg": None}

    achievements = _compute_achievements(class_rank, improvement, summary)

    return {
        "status": "success",
        "student_id": login_id,
        "display_name": user.display_name,
        "summary": summary,
        "class_rank": class_rank,
        "improvement": improvement,
        "skill_breakdown": skills,
        "recent_submissions": history[:5],
        "achievements": achievements,
    }


# ---------------------------------------------------------------------------
# Submissions — all student's evaluated submissions
# ---------------------------------------------------------------------------

@router.get("/submissions")
def student_submissions(
    topic: Optional[str] = None,
    limit: int = 50,
    user: TokenPayload = Depends(require_student),
):
    """List all of the student's evaluated submissions."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    db_id = _resolve_db_student_id(login_id)
    all_ids = _get_all_db_ids(login_id)

    history = get_score_history(db_id, topic_tag=topic, limit=limit)

    db = get_db()
    detailed_results = []
    if db.available:
        # Query using all possible ID variants
        placeholders = ", ".join(["%s"] * len(all_ids))
        rows = db.execute(
            f"""
            SELECT submission_id, assignment_type, file,
                   final_score, max_score, percentage,
                   feedback, flag_score, flag_reasons,
                   percentile, improvement_delta, trend,
                   batch_id, evaluated_at
            FROM evaluation_results
            WHERE submission_id IN ({placeholders})
            ORDER BY evaluated_at DESC
            LIMIT %s
            """,
            [*all_ids, limit],
        )
        for r in (rows or []):
            entry = dict(r)
            if isinstance(entry.get("feedback"), str):
                entry["feedback"] = json.loads(entry["feedback"])
            if isinstance(entry.get("flag_reasons"), str):
                entry["flag_reasons"] = json.loads(entry["flag_reasons"])
            if entry.get("evaluated_at"):
                entry["evaluated_at"] = entry["evaluated_at"].isoformat()
            if entry.get("flag_score") and entry["flag_score"] > 0.5:
                entry["integrity_status"] = "under_review"
            else:
                entry["integrity_status"] = "clean"
            entry.pop("flag_reasons", None)
            detailed_results.append(entry)

    return {
        "status": "success",
        "student_id": login_id,
        "submissions": detailed_results if detailed_results else _history_to_submissions(history),
        "total_count": len(detailed_results) if detailed_results else len(history),
    }


# ---------------------------------------------------------------------------
# Submission Detail — single submission with full feedback
# ---------------------------------------------------------------------------

@router.get("/submissions/{submission_id}")
def student_submission_detail(
    submission_id: str,
    user: TokenPayload = Depends(require_student),
):
    """Detailed view of a single submission with AI-generated feedback."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    all_ids = _get_all_db_ids(login_id)

    db = get_db()
    if not db.available:
        raise HTTPException(503, "Database unavailable")

    placeholders = ", ".join(["%s"] * len(all_ids))
    row = db.execute_one(
        f"""
        SELECT submission_id, assignment_type, file,
               final_score, max_score, percentage,
               feedback, flag_score, flag_reasons,
               percentile, improvement_delta, trend,
               batch_id, evaluated_at
        FROM evaluation_results
        WHERE batch_id = %s AND submission_id IN ({placeholders})
        """,
        [submission_id, *all_ids],
    )

    if not row:
        raise HTTPException(404, "Submission not found")

    result = dict(row)
    if isinstance(result.get("feedback"), str):
        result["feedback"] = json.loads(result["feedback"])
    if isinstance(result.get("flag_reasons"), str):
        result["flag_reasons"] = json.loads(result["flag_reasons"])
    if result.get("evaluated_at"):
        result["evaluated_at"] = result["evaluated_at"].isoformat()

    if result.get("flag_score") and result["flag_score"] > 0.5:
        result["integrity_status"] = "under_review"
    else:
        result["integrity_status"] = "clean"
    result.pop("flag_reasons", None)

    class_avg = None
    if result.get("batch_id"):
        avg_row = db.execute_one(
            "SELECT AVG(percentage) as avg_pct FROM evaluation_results WHERE batch_id = %s",
            [result["batch_id"]],
        )
        if avg_row and avg_row.get("avg_pct"):
            class_avg = round(float(avg_row["avg_pct"]), 1)
    result["class_average"] = class_avg

    return {"status": "success", "submission": result}


# ---------------------------------------------------------------------------
# Progress — score trends and skill development
# ---------------------------------------------------------------------------

@router.get("/progress")
def student_progress(user: TokenPayload = Depends(require_student)):
    """Student's progress over time."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    db_id = _resolve_db_student_id(login_id)

    history = get_score_history(db_id, limit=50)
    summary = get_student_summary(db_id)
    skills = get_skill_breakdown(db_id)
    class_rank = get_class_percentile(db_id)

    if history:
        latest_score = history[0]["score"]
        latest_topic = history[0].get("topic_tag", "")
        improvement = get_improvement_delta(
            db_id, topic_tag=latest_topic, current_score=latest_score
        )
    else:
        improvement = {"delta": None, "trend": "no data", "prev_avg": None}

    return {
        "status": "success",
        "student_id": login_id,
        "score_history": history,
        "summary": summary,
        "skill_breakdown": skills,
        "class_rank": class_rank,
        "improvement": improvement,
    }


# ---------------------------------------------------------------------------
# Leaderboard — anonymized class ranking
# ---------------------------------------------------------------------------

@router.get("/leaderboard")
def student_leaderboard(user: TokenPayload = Depends(require_student)):
    """Anonymized class leaderboard."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    db = get_db()
    if not db.available:
        raise HTTPException(503, "Database unavailable")

    rows = db.execute(
        """
        SELECT student_id,
               AVG(score) as avg_score,
               COUNT(*) as submission_count
        FROM student_scores
        GROUP BY student_id
        ORDER BY AVG(score) DESC
        """
    )

    leaderboard = []
    my_rank = None
    for i, row in enumerate(rows or []):
        entry = dict(row)
        rank = i + 1
        is_self = _is_own_id(entry["student_id"], login_id)

        if is_self:
            my_rank = rank

        leaderboard.append({
            "rank": rank,
            "display_name": "You" if is_self else f"Student #{rank}",
            "avg_score": round(float(entry["avg_score"]), 1),
            "submission_count": entry["submission_count"],
            "is_self": is_self,
        })

    return {
        "status": "success",
        "leaderboard": leaderboard,
        "my_rank": my_rank,
        "total_students": len(leaderboard),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_achievements(class_rank: dict, improvement: dict, summary: dict) -> list:
    """Compute dynamic achievement badges for a student."""
    achievements = []

    if class_rank.get("percentile", 0) >= 90:
        achievements.append({
            "icon": "workspace_premium",
            "title": "Top 10% Achievement",
            "description": "Outstanding performance ranking in the top 10% of the class.",
            "color": "amber",
        })
    elif class_rank.get("percentile", 0) >= 75:
        achievements.append({
            "icon": "emoji_events",
            "title": "Top 25% Performer",
            "description": "Consistently strong performance in class evaluations.",
            "color": "violet",
        })

    if improvement.get("trend") == "improving":
        delta = improvement.get("delta", 0) or 0
        achievements.append({
            "icon": "trending_up",
            "title": "On the Rise",
            "description": f"+{delta:.1f} points improvement over recent submissions.",
            "color": "emerald",
        })

    total = summary.get("total_submissions", 0)
    if total >= 10:
        achievements.append({
            "icon": "military_tech",
            "title": "Dedicated Submitter",
            "description": f"{total} submissions completed. Consistent effort!",
            "color": "blue",
        })
    elif total >= 5:
        achievements.append({
            "icon": "verified",
            "title": "Getting Started",
            "description": f"{total} submissions completed. Keep going!",
            "color": "blue",
        })

    best = summary.get("best_score", 0)
    if best >= 95:
        achievements.append({
            "icon": "stars",
            "title": "Near Perfect Score",
            "description": f"Achieved {best:.0f}/100 on a submission.",
            "color": "amber",
        })

    return achievements


def _history_to_submissions(history: list) -> list:
    """Convert score history entries to submission-like format."""
    return [
        {
            "submission_id": h.get("student_id", ""),
            "assignment_type": "unknown",
            "file": h.get("assignment_id", ""),
            "final_score": h.get("score", 0),
            "max_score": 100,
            "percentage": h.get("score", 0),
            "feedback": [],
            "integrity_status": "clean",
            "evaluated_at": h.get("submitted_at", ""),
            "topic_tag": h.get("topic_tag", ""),
        }
        for h in history
    ]
