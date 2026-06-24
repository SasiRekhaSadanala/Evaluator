"""
Student profile tracker + cohort normalizer.

Provides:
- Per-student score history with improvement deltas
- Class-wide percentile ranking
- Trend analysis ("improving", "stable", "declining")
"""

from typing import Any, Dict, List, Optional

import numpy as np

from backend.core.services.database import get_db


# ---------------------------------------------------------------------------
# Score recording
# ---------------------------------------------------------------------------

def record_score(
    student_id: str,
    assignment_id: str,
    score: float,
    topic_tag: str = "",
) -> bool:
    """
    Record a student's score for an assignment.

    Returns True if recorded successfully, False if DB unavailable.
    """
    db = get_db()
    if not db.available:
        return False

    db.execute(
        """
        INSERT INTO student_scores (student_id, assignment_id, topic_tag, score)
        VALUES (%s, %s, %s, %s)
        """,
        [student_id, assignment_id, topic_tag or "", score],
    )
    return True


# ---------------------------------------------------------------------------
# Improvement delta
# ---------------------------------------------------------------------------

def get_improvement_delta(
    student_id: str,
    topic_tag: str,
    current_score: float,
) -> Dict[str, Any]:
    """
    Compute improvement delta vs. the student's recent history.

    Compares current score against the average of the student's last 5
    submissions on the same topic.

    Returns:
        {
            "delta": float | None,
            "trend": "improving" | "declining" | "stable" | "first submission",
            "prev_avg": float | None
        }
    """
    db = get_db()
    if not db.available:
        return {"delta": None, "trend": "first submission", "prev_avg": None}

    rows = db.execute(
        """
        SELECT score FROM student_scores
        WHERE student_id = %s AND topic_tag = %s
        ORDER BY submitted_at DESC
        LIMIT 5
        """,
        [student_id, topic_tag or ""],
    )

    if not rows:
        return {"delta": None, "trend": "first submission", "prev_avg": None}

    prev_avg = sum(r["score"] for r in rows) / len(rows)
    delta = current_score - prev_avg

    if delta > 5:
        trend = "improving"
    elif delta < -5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "delta": round(delta, 1),
        "trend": trend,
        "prev_avg": round(prev_avg, 1),
    }


# ---------------------------------------------------------------------------
# Cohort percentile
# ---------------------------------------------------------------------------

def compute_percentile(student_score: float, all_scores: List[float]) -> int:
    """
    Compute a student's percentile rank within the class.

    Args:
        student_score: The student's score.
        all_scores: List of all student scores for the same assignment.

    Returns:
        Percentile rank (0–100).
    """
    if not all_scores:
        return 0

    arr = np.array(all_scores)
    return int(np.sum(arr <= student_score) / len(arr) * 100)


def compute_percentiles_for_cohort(
    results: Dict[str, float],
) -> Dict[str, int]:
    """
    Compute percentile ranks for all students in a cohort.

    Args:
        results: Dict mapping student_id → score.

    Returns:
        Dict mapping student_id → percentile rank.
    """
    all_scores = list(results.values())
    return {
        student_id: compute_percentile(score, all_scores)
        for student_id, score in results.items()
    }


# ---------------------------------------------------------------------------
# Score history
# ---------------------------------------------------------------------------

def get_score_history(
    student_id: str,
    topic_tag: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """
    Get a student's score history.

    Args:
        student_id: Student identifier.
        topic_tag: Optional filter by topic.
        limit: Maximum number of records.

    Returns:
        List of score records, newest first.
    """
    db = get_db()
    if not db.available:
        return []

    if topic_tag:
        rows = db.execute(
            """
            SELECT assignment_id, topic_tag, score, submitted_at
            FROM student_scores
            WHERE student_id = %s AND topic_tag = %s
            ORDER BY submitted_at DESC
            LIMIT %s
            """,
            [student_id, topic_tag, limit],
        )
    else:
        rows = db.execute(
            """
            SELECT assignment_id, topic_tag, score, submitted_at
            FROM student_scores
            WHERE student_id = %s
            ORDER BY submitted_at DESC
            LIMIT %s
            """,
            [student_id, limit],
        )

    result = []
    for r in (rows or []):
        entry = dict(r)
        if entry.get("submitted_at"):
            entry["submitted_at"] = entry["submitted_at"].isoformat()
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Skill breakdown (per-topic averages)
# ---------------------------------------------------------------------------

def get_skill_breakdown(student_id: str) -> List[Dict]:
    """
    Get a student's average score grouped by topic_tag.

    Returns:
        List of {topic_tag, avg_score, submission_count}, sorted by count desc.
    """
    db = get_db()
    if not db.available:
        return []

    rows = db.execute(
        """
        SELECT topic_tag,
               ROUND(AVG(score)::numeric, 1) AS avg_score,
               COUNT(*)::int                  AS submission_count
        FROM student_scores
        WHERE student_id = %s AND topic_tag IS NOT NULL AND topic_tag != ''
        GROUP BY topic_tag
        ORDER BY submission_count DESC
        """,
        [student_id],
    )

    result = []
    for r in (rows or []):
        entry = dict(r)
        entry["avg_score"] = float(entry["avg_score"])
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Class-wide percentile
# ---------------------------------------------------------------------------

def get_class_percentile(student_id: str) -> Dict[str, Any]:
    """
    Compute a student's percentile rank across the entire class.

    Uses each student's average score over all assignments as their
    representative score, then computes the percentile for the target student.

    Returns:
        {
            "percentile": int (0–100),
            "class_size": int,
            "student_avg": float | None
        }
    """
    db = get_db()
    if not db.available:
        return {"percentile": 0, "class_size": 0, "student_avg": None}

    # All students' averages
    rows = db.execute(
        """
        SELECT student_id, AVG(score) AS avg_score
        FROM student_scores
        GROUP BY student_id
        """
    )

    if not rows:
        return {"percentile": 0, "class_size": 0, "student_avg": None}

    averages = {r["student_id"]: float(r["avg_score"]) for r in rows}
    student_avg = averages.get(student_id)

    if student_avg is None:
        return {"percentile": 0, "class_size": len(averages), "student_avg": None}

    all_avgs = list(averages.values())
    percentile = compute_percentile(student_avg, all_avgs)

    return {
        "percentile": percentile,
        "class_size": len(averages),
        "student_avg": round(student_avg, 1),
    }


# ---------------------------------------------------------------------------
# Student summary stats
# ---------------------------------------------------------------------------

def get_student_summary(student_id: str) -> Dict[str, Any]:
    """
    Compute summary statistics for a student.

    Returns:
        {
            "total_submissions": int,
            "average_score": float,
            "best_score": float,
            "worst_score": float,
            "cumulative_grade": str,   # e.g. "A-", "B+", "C"
            "gpa": float,              # 4.0 scale
        }
    """
    db = get_db()
    if not db.available:
        return {
            "total_submissions": 0, "average_score": 0,
            "best_score": 0, "worst_score": 0,
            "cumulative_grade": "N/A", "gpa": 0.0,
        }

    row = db.execute_one(
        """
        SELECT COUNT(*)::int AS total,
               ROUND(AVG(score)::numeric, 1) AS avg_score,
               MAX(score) AS best,
               MIN(score) AS worst
        FROM student_scores
        WHERE student_id = %s
        """,
        [student_id],
    )

    if not row or row["total"] == 0:
        return {
            "total_submissions": 0, "average_score": 0,
            "best_score": 0, "worst_score": 0,
            "cumulative_grade": "N/A", "gpa": 0.0,
        }

    avg = float(row["avg_score"])
    grade, gpa = _score_to_grade(avg)

    return {
        "total_submissions": row["total"],
        "average_score": avg,
        "best_score": float(row["best"]),
        "worst_score": float(row["worst"]),
        "cumulative_grade": grade,
        "gpa": gpa,
    }


def _score_to_grade(score: float):
    """Convert a numeric score (0-100) to letter grade + GPA."""
    if score >= 93:
        return "A", 4.0
    elif score >= 90:
        return "A-", 3.7
    elif score >= 87:
        return "B+", 3.3
    elif score >= 83:
        return "B", 3.0
    elif score >= 80:
        return "B-", 2.7
    elif score >= 77:
        return "C+", 2.3
    elif score >= 73:
        return "C", 2.0
    elif score >= 70:
        return "C-", 1.7
    elif score >= 67:
        return "D+", 1.3
    elif score >= 63:
        return "D", 1.0
    elif score >= 60:
        return "D-", 0.7
    else:
        return "F", 0.0


def format_report_card(
    student_id: str,
    score: float,
    percentile: int,
    delta: Optional[float],
) -> str:
    """
    Format a human-readable report card line.

    Example: "Score: 74/100 · Top 32% of class · +11 points vs your last 3 submissions"
    """
    parts = [f"Score: {score:.0f}/100"]

    top_pct = 100 - percentile
    parts.append(f"Top {top_pct}% of class")

    if delta is not None:
        sign = "+" if delta >= 0 else ""
        parts.append(f"{sign}{delta:.0f} points vs recent average")

    return " · ".join(parts)
