"""Evaluation routes for the API."""

import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile

from backend.app.schemas import EvaluationRequest, EvaluationResponse, RubricConfig
from backend.app.services import EvaluatorService

router = APIRouter(prefix="/api", tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(
    assignment_type: str = Form(
        ...,
        description="Type of assignment: code, content, or mixed",
    ),
    problem_statement: Optional[str] = Form(
        None,
        description="Problem statement for code assignments",
    ),
    ideal_reference: Optional[str] = Form(
        None,
        description="Reference content for content assignments",
    ),
    rubric_json: Optional[str] = Form(
        None,
        description="Custom rubric as JSON string (optional)",
    ),
    files: List[UploadFile] = File(
        ...,
        description="Student submission files",
    ),
) -> EvaluationResponse:
    """
    Evaluate student submissions.

    Accepts multipart form data with:
    - **assignment_type**: Type of assignment (code, content, or mixed)
    - **problem_statement**: Problem description for code assignments
    - **ideal_reference**: Reference content for content assignments
    - **rubric_json**: Custom rubric as JSON (optional, uses default if not provided)
    - **files**: Student submission files (.py, .cpp, .cc, .cxx, .h, .hpp, .txt, .pdf)

    Returns evaluation results with scores, feedback, and CSV export paths.

    Example usage:
    ```python
    files = [
        ("files", open("submission1.py", "rb")),
        ("files", open("submission2.py", "rb")),
    ]
    data = {
        "assignment_type": "code",
        "problem_statement": "Write a factorial function",
    }
    response = requests.post("http://localhost:8000/api/evaluate", files=files, data=data)
    ```
    """
    # Validate file types
    ALLOWED_EXTENSIONS = {".py", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".txt", ".pdf"}
    for file in files:
        ext = "." + file.filename.lower().split(".")[-1] if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Allowed: .py, .cpp, .cc, .cxx, .h, .hpp, .txt, .pdf"
            )

    # Content inspection is deferred to evaluation agents to avoid duplication.

    # Create temporary directory for submissions
    temp_dir = tempfile.mkdtemp(prefix="submissions_")

    try:
        # Save uploaded files to temp directory
        for file in files:
            file_path = Path(temp_dir) / file.filename
            with open(file_path, "wb") as f:
                f.write(file.file.read())

        # Parse custom rubric if provided
        rubric = None
        if rubric_json:
            try:
                rubric_dict = json.loads(rubric_json)
                rubric = RubricConfig(**rubric_dict)
            except (json.JSONDecodeError, ValueError):
                # Invalid JSON, proceed with default rubric
                pass

        # Create evaluation request
        request = EvaluationRequest(
            assignment_type=assignment_type,
            submission_folder=temp_dir,
            problem_statement=problem_statement,
            ideal_reference=ideal_reference,
            rubric=rubric,
        )

        # Evaluate via service layer
        service = EvaluatorService()
        response = service.evaluate(request)

        return response

    except Exception as e:
        return EvaluationResponse(
            status="error",
            message="Evaluation failed",
            error_message=str(e),
        )

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
