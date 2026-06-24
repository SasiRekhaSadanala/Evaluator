"""
Persistent evaluation results store.

Saves full evaluation results (with feedback, flags, etc.) to PostgreSQL
so they survive across browser sessions and new evaluations.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from backend.core.services.database import get_db


def save_evaluation_batch(
    results: List[Dict[str, Any]],
    summary: Optional[Dict[str, Any]],
    csv_output_path: Optional[str] = None,
    csv_detailed_output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Save a complete evaluation batch to the database.

    Args:
        results: List of EvaluationResultItem dicts
        summary: Summary statistics dict
        csv_output_path: Path to summary CSV
        csv_detailed_output_path: Path to detailed CSV

    Returns:
        batch_id if saved, None if DB unavailable.
    """
    db = get_db()
    if not db.available:
        return None

    batch_id = uuid.uuid4().hex[:16]

    # Save batch summary
    if summary:
        db.execute(
            """
            INSERT INTO evaluation_batches
                (batch_id, assignment_type, total_submissions, average_score,
                 average_percentage, highest_score, lowest_score,
                 csv_output_path, csv_detailed_output_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                batch_id,
                results[0].get("assignment_type", "") if results else "",
                summary.get("total_submissions", 0),
                summary.get("average_score", 0),
                summary.get("average_percentage", 0),
                summary.get("highest_score", 0),
                summary.get("lowest_score", 0),
                csv_output_path,
                csv_detailed_output_path,
            ],
        )

    # Save individual results
    for r in results:
        feedback_json = json.dumps(r.get("feedback", []))
        flag_reasons_json = json.dumps(r.get("flag_reasons") or [])

        db.execute(
            """
            INSERT INTO evaluation_results
                (batch_id, submission_id, assignment_type, file,
                 final_score, max_score, percentage, feedback,
                 flag_score, flag_reasons, percentile,
                 improvement_delta, trend)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s, %s, %s)
            """,
            [
                batch_id,
                r.get("submission_id", ""),
                r.get("assignment_type", ""),
                r.get("file", ""),
                r.get("final_score", 0),
                r.get("max_score", 100),
                r.get("percentage", 0),
                feedback_json,
                r.get("flag_score"),
                flag_reasons_json,
                r.get("percentile"),
                r.get("improvement_delta"),
                r.get("trend"),
            ],
        )

    return batch_id


def get_all_evaluations(limit: int = 200) -> Dict[str, Any]:
    """
    Retrieve all evaluation batches with their results.

    Returns the same shape as EvaluationResponse so the frontend
    can consume it directly.
    """
    db = get_db()
    if not db.available:
        return {"batches": [], "all_results": []}

    # Get all individual results ordered by time
    rows = db.execute(
        """
        SELECT submission_id, assignment_type, file,
               final_score, max_score, percentage,
               feedback, flag_score, flag_reasons,
               percentile, improvement_delta, trend,
               batch_id, evaluated_at
        FROM evaluation_results
        ORDER BY evaluated_at DESC
        LIMIT %s
        """,
        [limit],
    )

    results = []
    for r in (rows or []):
        entry = dict(r)
        # Convert JSONB fields
        if isinstance(entry.get("feedback"), str):
            entry["feedback"] = json.loads(entry["feedback"])
        if isinstance(entry.get("flag_reasons"), str):
            entry["flag_reasons"] = json.loads(entry["flag_reasons"])
        if entry.get("evaluated_at"):
            entry["evaluated_at"] = entry["evaluated_at"].isoformat()
        results.append(entry)

    # Get batch summaries
    batch_rows = db.execute(
        """
        SELECT batch_id, assignment_type, total_submissions,
               average_score, average_percentage, highest_score,
               lowest_score, csv_output_path, csv_detailed_output_path,
               evaluated_at
        FROM evaluation_batches
        ORDER BY evaluated_at DESC
        LIMIT 50
        """
    )

    batches = []
    for b in (batch_rows or []):
        entry = dict(b)
        if entry.get("evaluated_at"):
            entry["evaluated_at"] = entry["evaluated_at"].isoformat()
        batches.append(entry)

    return {"batches": batches, "all_results": results}
