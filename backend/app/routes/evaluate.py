"""Evaluation routes for the API."""

import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from backend.app.schemas import EvaluationRequest, EvaluationResponse, RubricConfig
from backend.app.services import EvaluatorService
from utils.llm_service import LLMService

router = APIRouter(prefix="/api", tags=["evaluation"])

@router.get("/download/{filename}")
def download_csv(filename: str):
    """Download exported CSV file."""
    # Ensure filename is safe (basic check)
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Invalid filename")
    
    file_path = Path("outputs") / filename
    if not file_path.exists():
        raise HTTPException(404, "File not found")
        
    return FileResponse(file_path, media_type="text/csv", filename=filename)


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
    rubric_content: Optional[str] = Form(
        None,
        description="Custom rubric as plain text or JSON string (optional)",
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
    - **rubric_content**: Custom rubric as text or JSON (optional, uses default if not provided)
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
        rubric_warning = None
        if rubric_content:
            try:
                # Try strict JSON parsing first
                rubric_dict = json.loads(rubric_content)
                rubric = RubricConfig(**rubric_dict)
            except (json.JSONDecodeError, ValueError):
                # If not JSON or invalid JSON structure, treat as plain text and use LLM
                print("Rubric JSON parse failed, attempting LLM parsing of text rubric...")
                try:
                    llm_service = LLMService()
                    parsed_dict = llm_service.parse_rubric_text(rubric_content)
                    if parsed_dict:
                        rubric = RubricConfig(**parsed_dict)
                    else:
                        rubric_warning = "Failed to parse text rubric via LLM (returned None). Using default rubric."
                except Exception as e:
                    rubric_warning = f"Error during LLM rubric parsing: {e}. Using default rubric."
                    print(rubric_warning)

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

        # Convert local file paths to download URLs
        # Assuming frontend is on same host/port for relative links, or construct full URL
        # For simplicity, we'll return full URLs assuming localhost:8000 for now, 
        # but in prod this should be dynamic.
        base_url = "http://localhost:8000/api/download"
        
        if response.csv_output_path:
            filename = Path(response.csv_output_path).name
            response.csv_output_path = f"{base_url}/{filename}"
            
        if response.csv_detailed_output_path:
            filename = Path(response.csv_detailed_output_path).name
            response.csv_detailed_output_path = f"{base_url}/{filename}"

        if rubric_warning:
            response.message += f" | Warning: {rubric_warning}"

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
