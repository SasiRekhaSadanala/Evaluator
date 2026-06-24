"""API routes for the human review queue."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.services.review_queue import (
    get_pending_reviews,
    get_review_by_id,
    set_teacher_override,
    get_queue_stats,
)


router = APIRouter(prefix="/api/reviews", tags=["reviews"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class OverrideRequest(BaseModel):
    """Request body for teacher score override."""
    teacher_score: float = Field(..., ge=0, le=100, description="Teacher-assigned score")
    teacher_notes: str = Field(default="", description="Optional notes from teacher")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
def list_reviews(
    assignment_id: Optional[str] = None,
    status: str = "pending",
    limit: int = 50,
):
    """
    List review queue items.

    Query params:
    - assignment_id: Filter by assignment
    - status: 'pending' (default) or 'reviewed'
    - limit: Max items to return
    """
    reviews = get_pending_reviews(assignment_id=assignment_id, limit=limit)
    return {
        "status": "success",
        "count": len(reviews),
        "reviews": reviews,
    }


@router.get("/stats")
def review_stats():
    """Get review queue statistics."""
    stats = get_queue_stats()
    return {"status": "success", **stats}


@router.get("/{review_id}")
def get_review(review_id: str):
    """Get a single review item by ID."""
    review = get_review_by_id(review_id)
    if not review:
        raise HTTPException(404, "Review not found")
    return {"status": "success", "review": review}


@router.post("/{review_id}/override")
def override_score(review_id: str, body: OverrideRequest):
    """
    Teacher overrides the auto-generated score.

    The original auto_score is preserved for tracking system accuracy.
    """
    updated = set_teacher_override(
        review_id,
        teacher_score=body.teacher_score,
        teacher_notes=body.teacher_notes,
    )
    if not updated:
        raise HTTPException(404, "Review not found or database unavailable")
    return {
        "status": "success",
        "message": f"Score overridden to {body.teacher_score}",
        "review": updated,
    }
