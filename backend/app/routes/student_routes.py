"""API routes for student profile and history."""

from typing import Optional

from fastapi import APIRouter

from backend.core.services.student_tracker import (
    get_score_history,
    get_improvement_delta,
    get_skill_breakdown,
    get_class_percentile,
    get_student_summary,
    format_report_card,
)


router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/{student_id}/profile")
def student_profile(student_id: str):
    """
    Comprehensive student profile endpoint.

    Returns everything the Student Profile page needs in a single call:
    - score_history: Last 20 submissions
    - improvement: Delta and trend vs recent average
    - class_rank: Percentile across all students
    - skill_breakdown: Per-topic average scores
    - summary: Aggregate stats (total, avg, best, worst, grade, GPA)
    """
    history = get_score_history(student_id, limit=20)

    # Improvement delta
    if history:
        latest_score = history[0]["score"]
        # Use topic from latest submission if available
        latest_topic = history[0].get("topic_tag", "")
        improvement = get_improvement_delta(
            student_id, topic_tag=latest_topic, current_score=latest_score
        )
    else:
        improvement = {"delta": None, "trend": "no data", "prev_avg": None}

    # Class rank
    class_rank = get_class_percentile(student_id)

    # Skill breakdown
    skills = get_skill_breakdown(student_id)

    # Summary stats
    summary = get_student_summary(student_id)

    # Dynamic achievements
    achievements = []
    if class_rank["percentile"] >= 90:
        achievements.append({
            "icon": "workspace_premium",
            "title": "Top 10% Achievement",
            "description": "Outstanding performance ranking in the top 10% of the class.",
            "color": "amber",
        })
    elif class_rank["percentile"] >= 75:
        achievements.append({
            "icon": "emoji_events",
            "title": "Top 25% Performer",
            "description": "Consistently strong performance in class evaluations.",
            "color": "violet",
        })

    if improvement.get("trend") == "improving":
        achievements.append({
            "icon": "trending_up",
            "title": "On the Rise",
            "description": f"+{improvement['delta']:.1f} points improvement over recent submissions.",
            "color": "emerald",
        })

    if summary["total_submissions"] >= 10:
        achievements.append({
            "icon": "military_tech",
            "title": "Dedicated Submitter",
            "description": f"{summary['total_submissions']} submissions completed. Consistent effort!",
            "color": "blue",
        })

    if summary["best_score"] >= 95:
        achievements.append({
            "icon": "stars",
            "title": "Near Perfect Score",
            "description": f"Achieved {summary['best_score']:.0f}/100 on a submission.",
            "color": "amber",
        })

    return {
        "status": "success",
        "student_id": student_id,
        "score_history": history,
        "improvement": improvement,
        "class_rank": class_rank,
        "skill_breakdown": skills,
        "summary": summary,
        "achievements": achievements,
    }


@router.get("/{student_id}/history")
def student_history(
    student_id: str,
    topic_tag: Optional[str] = None,
    limit: int = 20,
):
    """
    Get a student's score history with improvement deltas.

    Query params:
    - topic_tag: Filter by topic (optional)
    - limit: Max records to return (default 20)
    """
    history = get_score_history(student_id, topic_tag=topic_tag, limit=limit)

    # Compute running delta if history exists
    if history:
        scores = [h["score"] for h in history]
        latest = scores[0] if scores else 0
        delta_info = get_improvement_delta(
            student_id,
            topic_tag=topic_tag or "",
            current_score=latest,
        )
    else:
        delta_info = {"delta": None, "trend": "no data", "prev_avg": None}

    return {
        "status": "success",
        "student_id": student_id,
        "history": history,
        "improvement": delta_info,
    }


@router.get("/{student_id}/report")
def student_report(
    student_id: str,
    score: float = 0,
    percentile: int = 50,
    topic_tag: Optional[str] = None,
):
    """
    Generate a formatted report card for a student.

    Query params:
    - score: Current score
    - percentile: Percentile rank in class
    - topic_tag: Topic for improvement delta
    """
    delta_info = get_improvement_delta(
        student_id,
        topic_tag=topic_tag or "",
        current_score=score,
    )

    report = format_report_card(
        student_id=student_id,
        score=score,
        percentile=percentile,
        delta=delta_info["delta"],
    )

    return {
        "status": "success",
        "student_id": student_id,
        "report_card": report,
        "details": {
            "score": score,
            "percentile": percentile,
            "trend": delta_info["trend"],
            "delta": delta_info["delta"],
        },
    }
