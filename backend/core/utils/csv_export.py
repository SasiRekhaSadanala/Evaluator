import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


def export_results_to_csv(
    results: Dict[str, Dict[str, Any]],
    output_folder: str = "./outputs",
    filename: Optional[str] = None,
) -> str:
    """
    Export evaluation results to CSV file.

    Args:
        results: Dictionary of student name to evaluation results
        output_folder: Folder to save CSV file
        filename: CSV filename. If None, uses 'results.csv'

    Returns:
        Path to the created CSV file
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_filename = filename or "results.csv"
    csv_file_path = output_path / csv_filename

    if not results:
        raise ValueError("No results to export")

    # Prepare rows
    rows = []
    for student_name, evaluation in results.items():
        row = {
            "submission_id": student_name,
            "final_score": evaluation.get("final_score", "N/A"),
            "max_score": evaluation.get("max_score", 100),
            "feedback": _format_feedback_for_csv(
                evaluation.get("combined_feedback", [])
            ),
            "assignment_type": evaluation.get("assignment_type", "N/A"),
            "file": evaluation.get("file", "N/A"),
        }
        rows.append(row)

    # Write to CSV
    fieldnames = ["submission_id", "final_score", "max_score", "feedback", "assignment_type", "file"]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return str(csv_file_path)


def _format_feedback_for_csv(feedback_list: List[str]) -> str:
    """
    Format feedback list into a single CSV-safe string.

    Args:
        feedback_list: List of feedback strings

    Returns:
        Formatted feedback string
    """
    if not feedback_list:
        return ""

    # Join with semicolon separator for clarity
    return " | ".join(feedback_list)


def export_results_to_detailed_csv(
    results: Dict[str, Dict[str, Any]],
    output_folder: str = "./outputs",
    filename: Optional[str] = None,
) -> str:
    """
    Export evaluation results to a detailed CSV with separate columns per feedback item.

    Args:
        results: Dictionary of student name to evaluation results
        output_folder: Folder to save CSV file
        filename: CSV filename. If None, uses 'results_detailed.csv'

    Returns:
        Path to the created CSV file
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_filename = filename or "results_detailed.csv"
    csv_file_path = output_path / csv_filename

    if not results:
        raise ValueError("No results to export")

    # Prepare rows (one feedback per row)
    rows = []
    for student_name, evaluation in results.items():
        feedback_list = evaluation.get("combined_feedback", [])

        if feedback_list:
            for feedback_item in feedback_list:
                row = {
                    "submission_id": student_name,
                    "final_score": evaluation.get("final_score", "N/A"),
                    "max_score": evaluation.get("max_score", 100),
                    "feedback": feedback_item,
                    "assignment_type": evaluation.get("assignment_type", "N/A"),
                    "file": evaluation.get("file", "N/A"),
                }
                rows.append(row)
        else:
            row = {
                "submission_id": student_name,
                "final_score": evaluation.get("final_score", "N/A"),
                "max_score": evaluation.get("max_score", 100),
                "feedback": "No feedback available",
                "assignment_type": evaluation.get("assignment_type", "N/A"),
                "file": evaluation.get("file", "N/A"),
            }
            rows.append(row)

    # Write to CSV
    fieldnames = ["submission_id", "final_score", "max_score", "feedback", "assignment_type", "file"]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return str(csv_file_path)
