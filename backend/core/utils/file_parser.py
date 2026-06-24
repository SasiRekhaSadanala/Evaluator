import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
    supported_extensions = {".py", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".txt", ".pdf", ".html", ".htm"}
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
            # Security: Ensure we only process the direct file, no path traversal
            safe_name = os.path.basename(file_path.name)
            content = read_file(str(file_path))
            if content is not None:  # Only include supported files
                submissions[safe_name] = content

    return submissions


def read_submissions_by_type(folder_path: str) -> Dict[str, Dict[str, str]]:
    """
    Read all submissions organized by file type.

    For mixed evaluation, supports two modes:
    1. Two files per student (e.g., student.py + student.txt) — classic split
    2. Single file per student — auto-splits code and text content from one file

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
            safe_name = os.path.basename(file_path.name)
            content = read_file(str(file_path))
            if content is not None:
                # C++ and Python files are code
                if file_path.suffix.lower() in [".py", ".cpp", ".cc", ".cxx", ".h", ".hpp"]:
                    result["code"][safe_name] = content
                elif file_path.suffix.lower() in [".txt", ".pdf"]:
                    result["text"][safe_name] = content

    # ── Auto-split single files for mixed evaluation ──
    # If a student has code but no matching text (or vice versa), split their file
    _auto_split_single_files(result)

    return result


def _auto_split_single_files(result: Dict[str, Dict[str, str]]) -> None:
    """
    For students who submitted a single file, auto-split it into code + text.

    Modifies result dict in-place. Checks if a student has a code file but
    no matching text file (or vice versa), and splits the single file.
    """
    code_students = {
        _stem(f): f for f in result["code"]
    }
    text_students = {
        _stem(f): f for f in result["text"]
    }

    # Students with code but no text → split code file to extract prose
    for stem, code_file in code_students.items():
        if stem not in text_students:
            content = result["code"][code_file]
            code_part, text_part = split_mixed_content(content, code_file)
            if text_part and len(text_part.strip()) > 20:
                # Keep the full file as code (for AST analysis)
                # Add extracted prose as a virtual .txt entry
                virtual_txt = _stem(code_file) + ".txt"
                result["text"][virtual_txt] = text_part
                print(f"  ✓ Auto-split '{code_file}': extracted {len(text_part)} chars of prose content")

    # Students with text but no code → split text file to extract code blocks
    for stem, text_file in text_students.items():
        if stem not in code_students:
            content = result["text"][text_file]
            code_part, text_part = split_mixed_content(content, text_file)
            if code_part and len(code_part.strip()) > 20:
                # Add extracted code as a virtual .py entry
                virtual_py = _stem(text_file) + ".py"
                result["code"][virtual_py] = code_part
                # Update text to be only the prose portion
                if text_part and len(text_part.strip()) > 20:
                    result["text"][text_file] = text_part
                print(f"  ✓ Auto-split '{text_file}': extracted {len(code_part)} chars of code")


def _stem(filename: str) -> str:
    """Get filename stem (without extension)."""
    return Path(filename).stem


def split_mixed_content(content: str, filename: str) -> Tuple[str, str]:
    """
    Split a single file into code and prose portions.

    Handles three file types:
    - Python (.py): Extracts docstrings + comment blocks as prose
    - C++ (.cpp): Extracts block comments (/* */) + line comments (//) as prose
    - Text (.txt): Extracts fenced code blocks (```) + indented blocks as code

    Args:
        content: Full file content
        filename: Filename (used to determine file type)

    Returns:
        Tuple of (code_portion, text_portion)
    """
    ext = Path(filename).suffix.lower()

    if ext in [".py"]:
        return _split_python(content)
    elif ext in [".cpp", ".cc", ".cxx", ".h", ".hpp"]:
        return _split_cpp(content)
    elif ext in [".txt", ".pdf"]:
        return _split_text(content)
    else:
        return content, ""


def _split_python(content: str) -> Tuple[str, str]:
    """
    Extract prose from a Python file.

    Prose = docstrings (triple-quoted strings) + comment blocks (# lines).
    Code = everything else.
    """
    prose_parts = []
    code_lines = []
    lines = content.split("\n")

    in_docstring = False
    docstring_delim = None
    docstring_buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect docstring start/end
        if not in_docstring:
            # Check for docstring start (triple quotes)
            for delim in ['"""', "'''"]:
                if delim in stripped:
                    count = stripped.count(delim)
                    if count >= 2:
                        # Single-line docstring: """text"""
                        match = re.search(r'(\"\"\"|\'\'\')(.*?)\1', stripped)
                        if match:
                            prose_parts.append(match.group(2).strip())
                            code_lines.append(line)  # Keep in code too for AST
                        break
                    elif count == 1:
                        # Multi-line docstring starts
                        in_docstring = True
                        docstring_delim = delim
                        # Extract text after the opening delimiter
                        after = stripped.split(delim, 1)[1] if delim in stripped else ""
                        docstring_buffer = [after] if after else []
                        code_lines.append(line)  # Keep in code for AST
                        break
            else:
                # Regular line — check if it's a comment block
                if stripped.startswith("#"):
                    # Standalone comment (not inline)
                    comment_text = stripped.lstrip("#").strip()
                    if len(comment_text) > 10:  # Skip short markers like "# ---"
                        prose_parts.append(comment_text)
                    code_lines.append(line)
                else:
                    code_lines.append(line)
        else:
            # Inside a multi-line docstring
            if docstring_delim in stripped:
                # Docstring ends
                before = stripped.split(docstring_delim, 1)[0]
                docstring_buffer.append(before)
                prose_parts.append("\n".join(docstring_buffer).strip())
                docstring_buffer = []
                in_docstring = False
                docstring_delim = None
                code_lines.append(line)  # Keep for AST
            else:
                docstring_buffer.append(stripped)
                code_lines.append(line)  # Keep for AST

        i += 1

    # If docstring was never closed, flush buffer
    if docstring_buffer:
        prose_parts.append("\n".join(docstring_buffer).strip())

    code_portion = "\n".join(code_lines)
    text_portion = "\n\n".join(p for p in prose_parts if p)

    return code_portion, text_portion


def _split_cpp(content: str) -> Tuple[str, str]:
    """
    Extract prose from a C++ file.

    Prose = block comments (/* ... */) + consecutive // comment lines.
    Code = everything else.
    """
    prose_parts = []

    # Extract block comments /* ... */
    block_comments = re.findall(r'/\*\s*(.*?)\s*\*/', content, re.DOTALL)
    for comment in block_comments:
        cleaned = comment.strip()
        if len(cleaned) > 15:  # Skip short pragmatic comments
            prose_parts.append(cleaned)

    # Extract consecutive // comment blocks (3+ lines of // comments = prose)
    lines = content.split("\n")
    comment_block = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//"):
            comment_text = stripped.lstrip("/").strip()
            comment_block.append(comment_text)
        else:
            if len(comment_block) >= 3:
                # 3+ consecutive comment lines = likely prose explanation
                prose_parts.append("\n".join(comment_block))
            comment_block = []

    # Flush remaining
    if len(comment_block) >= 3:
        prose_parts.append("\n".join(comment_block))

    text_portion = "\n\n".join(p for p in prose_parts if p)
    return content, text_portion  # Keep full content as code for AST


def _split_text(content: str) -> Tuple[str, str]:
    """
    Extract code from a text/markdown file.

    Detects code via three strategies (in priority order):
    1. Fenced code blocks (```...```)
    2. Bare Python/C++ function definitions at column 0
    3. Indented blocks (4+ spaces after a blank line)

    This ensures code is extracted even when students paste functions
    without markdown formatting.
    """
    code_parts = []
    text_lines = []
    lines = content.split("\n")

    # ── Patterns that signal the start of a bare code block ──
    _CODE_START_PATTERNS = (
        "def ",           # Python function
        "class ",         # Python/C++ class
        "#include",       # C++ header
        "using namespace",# C++ namespace
        "import ",        # Python import (at top of code block)
    )

    def _is_code_continuation(line: str) -> bool:
        """Check if a line is part of a code block body."""
        if not line.strip():
            return True  # Blank lines inside code are OK
        if line[0] in (' ', '\t'):
            return True  # Indented = still inside function body
        # Decorators, comments
        stripped = line.strip()
        if stripped.startswith('@') or stripped.startswith('#'):
            return True
        return False

    def _is_code_start(line: str) -> bool:
        """Check if a line starts a new bare code block."""
        stripped = line.strip()
        return any(stripped.startswith(p) for p in _CODE_START_PATTERNS)

    in_fenced_block = False
    in_bare_code = False
    code_buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Strategy 1: Fenced code blocks ──
        if stripped.startswith("```"):
            # Flush any bare code block in progress
            if in_bare_code and code_buffer:
                code_parts.append("\n".join(code_buffer))
                code_buffer = []
                in_bare_code = False

            if not in_fenced_block:
                in_fenced_block = True
                code_buffer = []
            else:
                in_fenced_block = False
                if code_buffer:
                    code_parts.append("\n".join(code_buffer))
                code_buffer = []
            i += 1
            continue

        if in_fenced_block:
            code_buffer.append(line)
            i += 1
            continue

        # ── Strategy 2: Bare code blocks ──
        if in_bare_code:
            if _is_code_continuation(line):
                code_buffer.append(line)
                i += 1
                continue
            elif _is_code_start(line):
                # New function/class definition — still code
                code_buffer.append(line)
                i += 1
                continue
            else:
                # Non-indented prose line → code block ended
                # But only if we've seen real code (not just blank lines)
                real_code = [l for l in code_buffer if l.strip()]
                if real_code:
                    code_parts.append("\n".join(code_buffer))
                else:
                    text_lines.extend(code_buffer)
                code_buffer = []
                in_bare_code = False
                # Fall through to handle current line as text

        if _is_code_start(line):
            in_bare_code = True
            code_buffer = [line]
            i += 1
            continue

        # ── Strategy 3: Indented blocks ──
        if (line.startswith("    ") or line.startswith("\t")) and len(stripped) > 0:
            if i > 0 and (not lines[i - 1].strip() or lines[i - 1].startswith("    ")):
                code_parts.append(stripped)
                i += 1
                continue

        # ── Regular text ──
        text_lines.append(line)
        i += 1

    # Flush any remaining blocks
    if code_buffer:
        code_parts.append("\n".join(code_buffer))

    code_portion = "\n".join(code_parts)
    text_portion = "\n".join(text_lines)

    return code_portion, text_portion


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
    Extract clean student name from filename.

    Handles Moodle-style filenames like:
        'Deepak Paul Tirkey_35222_assignsubmission_onlinetext.html'
        → 'Deepak Paul Tirkey'

        'student_alice.py'
        → 'student_alice'

    Logic:
        1. Remove file extension
        2. If filename matches Moodle pattern (Name_DIGITS_assign...),
           extract only the name part before _DIGITS_
        3. Otherwise, use the full stem
        4. Append '_Result' suffix
    """
    import re
    name_without_ext = Path(filename).stem

    # Moodle pattern: Name_12345_assignsubmission_...
    # Match: everything before _<5+ digits>_
    moodle_match = re.match(r'^(.+?)_\d{4,}_', name_without_ext)
    if moodle_match:
        clean_name = moodle_match.group(1).strip()
        return f"{clean_name}_Result"

    return f"{name_without_ext}_Result"

