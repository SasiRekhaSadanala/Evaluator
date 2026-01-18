import os
from pathlib import Path
from typing import Dict, List, Optional


def read_file(file_path: str) -> Optional[str]:
    """
    Read a single student submission file.

    Args:
        file_path: Path to the file (.py, .txt, or .pdf)

    Returns:
        Clean text content, or None if file type is not supported
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check supported file types
    supported_extensions = {".py", ".txt", ".pdf"}
    if path.suffix.lower() not in supported_extensions:
        return None

    if path.suffix.lower() == ".pdf":
        return _read_pdf(file_path)

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
                elif file_path.suffix.lower() in [".txt", ".pdf"]:
                    result["text"][file_path.name] = content

    return result


def _read_pdf(file_path: str) -> Optional[str]:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted and cleaned text content
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return _clean_text(text)
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return None


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
    Extract student identifier from filename.
    Returns [stem]_Result to match user requirements.

    Args:
        filename: Name of submission file

    Returns:
        Refined submission identifier
    """
    name_without_ext = Path(filename).stem
    return f"{name_without_ext}_Result"
