import os
from pathlib import Path
from typing import Dict, List, Optional


def read_file(file_path: str) -> Optional[str]:
    """
    Read a single student submission file.

    Args:
        file_path: Path to the file (.py or .txt)

    Returns:
        Clean text content, or None if file type is not supported
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check supported file types
    supported_extensions = {".py", ".txt"}
    if path.suffix.lower() not in supported_extensions:
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return _clean_text(content)
    except UnicodeDecodeError:
        # Fallback to latin-1 encoding
        with open(file_path, "r", encoding="latin-1") as f:
            content = f.read()
        return _clean_text(content)


def read_folder(folder_path: str) -> Dict[str, str]:
    """
    Read all student submissions from a folder.

    Args:
        folder_path: Path to folder containing submissions

    Returns:
        Dictionary mapping file names to cleaned content.
        Skips unsupported file types.
    """
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    submissions = {}

    for file_path in folder.iterdir():
        if file_path.is_file():
            content = read_file(str(file_path))
            if content is not None:  # Only include supported files
                submissions[file_path.name] = content

    return submissions


def read_submissions_by_type(folder_path: str) -> Dict[str, Dict[str, str]]:
    """
    Read all submissions organized by file type.

    Args:
        folder_path: Path to folder containing submissions

    Returns:
        Dictionary with 'code' and 'text' keys, each containing
        a dict of file names to content.
    """
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    result = {"code": {}, "text": {}}

    for file_path in folder.iterdir():
        if file_path.is_file():
            content = read_file(str(file_path))
            if content is not None:
                if file_path.suffix.lower() == ".py":
                    result["code"][file_path.name] = content
                elif file_path.suffix.lower() == ".txt":
                    result["text"][file_path.name] = content

    return result


def _clean_text(content: str) -> str:
    """
    Clean text content: remove extra whitespace, normalize line endings.

    Args:
        content: Raw file content

    Returns:
        Cleaned text content
    """
    # Normalize line endings to \n
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Strip leading/trailing whitespace
    content = content.strip()

    return content


def get_student_name_from_filename(filename: str) -> str:
    """
    Extract student name from filename.
    Assumes format: lastname_firstname_submission.ext or student_id.ext

    Args:
        filename: Name of submission file

    Returns:
        Student identifier or original filename if parsing fails
    """
    name_without_ext = Path(filename).stem

    # Handle underscore-separated names
    if "_" in name_without_ext:
        parts = name_without_ext.split("_")
        # Remove common suffixes like "submission", "code", etc.
        cleaned = [p for p in parts if p.lower() not in ["submission", "code", "draft"]]
        if cleaned:
            return " ".join(cleaned).title()

    return name_without_ext
