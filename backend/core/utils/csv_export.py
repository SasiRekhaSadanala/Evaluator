import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def _clean_student_name(raw_name: str) -> str:
    """
    Strip Moodle metadata and _Result suffix from student names.
    'Deeksha Suresh_34567_Result' → 'Deeksha Suresh'
    'student_alice_Result' → 'student_alice'
    """
    name = raw_name.replace("_Result", "")
    # Strip Moodle ID: Name_34567 → Name
    name = re.sub(r'_\d{4,6}$', '', name)
    return name.strip()


def _strip_formatting(text: str) -> str:
    """Remove all emoji, markdown bold/headers, and bullet markers from text."""
    # Strip markdown bold
    text = text.replace("**", "")
    # Strip common emojis
    for emoji in ["🏆", "✅", "📝", "⚠️", "❌", "💪", "📋", "🎯", "🤖", "→", "✓", "ℹ", "##"]:
        text = text.replace(emoji, "")
    # Strip any remaining emoji (unicode ranges)
    text = re.sub(
        r'[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
        r'\U0000200D\U00002640\U00002642]+', '', text
    )
    # Collapse whitespace
    text = " ".join(text.split()).strip()
    return text


def _build_human_feedback(evaluation: Dict[str, Any]) -> str:
    """
    Build a clean, human-readable feedback paragraph from evaluation data.

    The output is a natural message about:
    - Score breakdown (why marks were gained/lost)
    - What topics the student missed
    - How they can improve (specific to their weaknesses)
    - The AI's personalized review (if available)

    No emoji, no markdown, no section headers, no scores.
    """
    combined = evaluation.get("combined_feedback", [])
    missing_concepts = []
    improvements = []
    ai_review = ""

    if combined and isinstance(combined, list):
        for line in combined:
            if not isinstance(line, str):
                continue

            clean = _strip_formatting(line)
            if not clean:
                continue

            # Extract AI review paragraph
            if "AI Analysis:" in line or "AI Evaluator" in line:
                ai_text = re.sub(
                    r'^.*?(?:AI Analysis:|AI Evaluator)\s*', '', line, flags=re.IGNORECASE
                )
                ai_text = _strip_formatting(ai_text).strip()
                if ai_text and len(ai_text) > 20:
                    ai_review = ai_text
                continue

            # Skip score breakdown line (not needed in CSV)
            if "Score Breakdown" in line:
                continue

            # Extract missing topics
            if "missing" in line.lower() and "topic" in line.lower():
                match = re.search(r'missing\s+topics?[:\s]+(.+)', clean, re.IGNORECASE)
                if match:
                    topics = [t.strip() for t in match.group(1).split(",") if t.strip()]
                    missing_concepts.extend(topics)
                continue

            # Skip covered topics line, overall assessment, strengths, header lines
            if any(skip in line.lower() for skip in [
                "topics covered", "excellent work", "good summary",
                "adequate summary", "needs improvement", "insufficient",
                "strengths", "how to improve",
                "outstanding summary", "you've captured", "your summary covers",
                "the summary is quite", "this submission does not"
            ]):
                continue

            # Extract improvement suggestions (lines starting with arrow markers)
            if line.strip().startswith("→") or line.strip().startswith("  →"):
                imp = _strip_formatting(line.strip().lstrip("→").strip())
                if imp and len(imp) > 10:
                    # Skip the "Include these missing topics" line since we handle that separately
                    if not imp.lower().startswith("include these missing"):
                        improvements.append(imp)
                continue

    # Build the human-readable feedback paragraph
    parts = []

    # Add what's missing
    if missing_concepts:
        seen = set()
        unique_missing = []
        for c in missing_concepts:
            cl = c.lower().strip()
            if cl not in seen and len(cl) > 1:
                seen.add(cl)
                unique_missing.append(c.strip())
        if unique_missing:
            if len(unique_missing) == 1:
                parts.append(f"You missed covering {unique_missing[0]} in your summary.")
            else:
                topics_str = ", ".join(unique_missing[:-1]) + " and " + unique_missing[-1]
                parts.append(f"You missed covering {topics_str} in your summary.")

    # Add improvement suggestions (these are now specific per student)
    if improvements:
        seen = set()
        unique_imps = []
        for imp in improvements:
            il = imp.lower().strip()
            if il not in seen:
                seen.add(il)
                unique_imps.append(imp)
        for imp in unique_imps[:3]:  # Max 3 improvement tips
            parts.append(imp)

    # Add AI review last — it's the most personalized touch
    if ai_review:
        parts.append(ai_review)

    # If nothing was extracted, build a basic fallback from scores
    if not parts:
        score = evaluation.get("final_score", 0)
        coverage = evaluation.get("concept_coverage", 0)

        if score >= 8:
            parts.append("Great work! Your summary demonstrates a strong understanding of the lecture material.")
        elif score >= 6:
            parts.append("You've covered the main ideas well. Try adding more detail about the specific concepts discussed in the lecture.")
        elif score >= 4:
            parts.append("Your summary touches on some topics but misses several key concepts from the lecture. Revisit the material and try to explain each concept in your own words.")
        else:
            parts.append("Your summary needs significant improvement. Please re-read or re-watch the lecture and try to cover all the main topics that were discussed.")

        if coverage > 0 and coverage < 60:
            parts.append(f"Your concept coverage was {round(coverage)}%, which means there are important topics you didn't address.")

    return " ".join(parts)


def export_results_to_csv(
    results: Dict[str, Dict[str, Any]],
    output_folder: str = "./outputs",
    filename: Optional[str] = None,
) -> str:
    """
    Export evaluation results to CSV file.

    Columns: student_name, concept_coverage, feedback, summary_text

    The feedback column contains a clean, human-readable message about
    what's missing and how to improve — no emoji, no markdown, no scores.

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
        clean_name = _clean_student_name(student_name)

        concept_coverage = evaluation.get("concept_coverage", 0)
        matched = evaluation.get("matched_concepts", 0)
        total = evaluation.get("total_concepts", 0)

        # Build coverage string: "57% (4/7)"
        if total:
            coverage_str = f"{round(concept_coverage)}% ({matched}/{total})"
        else:
            coverage_str = f"{round(concept_coverage)}%"

        # Get summary text
        summary = evaluation.get("summary_text", "")
        if summary:
            summary = " ".join(summary.split())

        # Build clean feedback
        feedback = _build_human_feedback(evaluation)

        # Score is already /10 from backend
        score_10 = evaluation.get("final_score", 0)

        row = {
            "student_name": clean_name,
            "score": score_10,
            "concept_coverage": coverage_str,
            "feedback": feedback,
            "summary_text": summary,
        }
        rows.append(row)

    # Sort by student name
    rows.sort(key=lambda r: r["student_name"])

    fieldnames = [
        "student_name",
        "score",
        "concept_coverage",
        "feedback",
        "summary_text",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return str(csv_file_path)


def export_results_to_detailed_csv(
    results: Dict[str, Dict[str, Any]],
    output_folder: str = "./outputs",
    filename: Optional[str] = None,
) -> str:
    """
    Export evaluation results to a detailed CSV.

    Same 4-column format as the main CSV but with fuller feedback.

    Args:
        results: Dictionary of student name to evaluation results
        output_folder: Folder to save CSV file
        filename: CSV filename

    Returns:
        Path to the created CSV file
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_filename = filename or "results_detailed.csv"
    csv_file_path = output_path / csv_filename

    if not results:
        raise ValueError("No results to export")

    rows = []
    for student_name, evaluation in results.items():
        clean_name = _clean_student_name(student_name)

        concept_coverage = evaluation.get("concept_coverage", 0)
        matched = evaluation.get("matched_concepts", 0)
        total = evaluation.get("total_concepts", 0)

        if total:
            coverage_str = f"{round(concept_coverage)}% ({matched}/{total})"
        else:
            coverage_str = f"{round(concept_coverage)}%"

        summary = evaluation.get("summary_text", "")
        if summary:
            summary = " ".join(summary.split())

        feedback = _build_human_feedback(evaluation)

        score_10 = evaluation.get("final_score", 0)

        row = {
            "student_name": clean_name,
            "score": score_10,
            "concept_coverage": coverage_str,
            "feedback": feedback,
            "summary_text": summary,
        }
        rows.append(row)

    rows.sort(key=lambda r: r["student_name"])

    fieldnames = [
        "student_name",
        "score",
        "concept_coverage",
        "feedback",
        "summary_text",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return str(csv_file_path)
