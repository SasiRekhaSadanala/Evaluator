"""
Submission index — PostgreSQL-backed storage for plagiarism detection.

Stores fingerprints and normalized code for every submission, enabling
both exact-match and fuzzy similarity checks against prior submissions
on the same assignment.
"""

import hashlib
import re
from typing import List, Optional

from backend.core.services.database import get_db


# ---------------------------------------------------------------------------
# Code normalization
# ---------------------------------------------------------------------------

def normalize_code(code: str) -> str:
    """
    Normalize code for comparison: strip comments, collapse whitespace.

    This makes renamed-variable copies look identical to originals.
    """
    # Strip Python-style comments
    code = re.sub(r"#.*", "", code)
    # Strip C-style single-line comments
    code = re.sub(r"//.*", "", code)
    # Strip C-style multi-line comments
    code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    # Collapse all whitespace
    code = re.sub(r"\s+", " ", code).strip()
    return code


def submission_fingerprint(code: str) -> str:
    """SHA-256 hash of normalized code."""
    return hashlib.sha256(normalize_code(code).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Index operations
# ---------------------------------------------------------------------------

def add_submission(
    assignment_id: str,
    student_id: str,
    code: str,
) -> Optional[str]:
    """
    Store a submission in the index.

    Args:
        assignment_id: Assignment identifier.
        student_id: Student identifier.
        code: Raw source code.

    Returns:
        The fingerprint string, or None if DB is unavailable.
    """
    db = get_db()
    if not db.available:
        return None

    fp = submission_fingerprint(code)
    norm = normalize_code(code)

    db.execute(
        """
        INSERT INTO submission_index (assignment_id, student_id, fingerprint, normalized_code)
        VALUES (%s, %s, %s, %s)
        """,
        [assignment_id, student_id, fp, norm],
    )
    return fp


def check_exact_match(
    assignment_id: str,
    student_id: str,
    code: str,
) -> Optional[str]:
    """
    Check if an identical submission exists from a different student.

    Returns:
        The student_id of the match, or None if no exact match.
    """
    db = get_db()
    if not db.available:
        return None

    fp = submission_fingerprint(code)
    row = db.execute_one(
        """
        SELECT student_id FROM submission_index
        WHERE assignment_id = %s
          AND fingerprint = %s
          AND student_id != %s
        LIMIT 1
        """,
        [assignment_id, fp, student_id],
    )
    return row["student_id"] if row else None


def get_prior_submissions(
    assignment_id: str,
    exclude_student_id: str,
) -> List[str]:
    """
    Get all prior normalized code submissions for an assignment
    (excluding the current student).

    Returns:
        List of normalized code strings.
    """
    db = get_db()
    if not db.available:
        return []

    rows = db.execute(
        """
        SELECT normalized_code FROM submission_index
        WHERE assignment_id = %s AND student_id != %s
        """,
        [assignment_id, exclude_student_id],
    )
    return [r["normalized_code"] for r in (rows or [])]
