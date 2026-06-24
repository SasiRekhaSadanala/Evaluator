"""Evaluation routes for the API."""

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from pydantic import BaseModel, Field

from backend.app.schemas import EvaluationRequest, EvaluationResponse, RubricConfig
from backend.app.services import EvaluatorService
from backend.core.services.evaluation_store import save_evaluation_batch, get_all_evaluations
from backend.core.services.database import get_db
from utils.llm_service import LLMService

router = APIRouter(prefix="/api", tags=["evaluation"])


class ScoreOverrideRequest(BaseModel):
    """Direct score override (for session-based reviews)."""
    student_id: str = Field(..., description="Student identifier, e.g. '23bds031_Result'")
    new_score: float = Field(..., ge=0, le=100, description="Teacher-assigned score")
    teacher_notes: str = Field(default="", description="Optional notes")


@router.post("/evaluations/score-override")
def direct_score_override(body: ScoreOverrideRequest):
    """
    Directly update a student's score in both student_scores
    and evaluation_results tables.

    Used by the frontend when review items come from session storage
    (no review_queue entry exists).
    """
    db = get_db()
    if not db.available:
        raise HTTPException(503, "Database unavailable")

    student_id = body.student_id
    new_score = body.new_score
    updated = {"student_scores": False, "evaluation_results": False}

    # Update student_scores (most recent entry for this student)
    try:
        db.execute(
            """
            UPDATE student_scores
            SET score = %s
            WHERE id = (
                SELECT id FROM student_scores
                WHERE student_id = %s
                ORDER BY submitted_at DESC
                LIMIT 1
            )
            """,
            [new_score, student_id],
        )
        updated["student_scores"] = True
        print(f"✓ Direct override → student_scores: {student_id} = {new_score}")
    except Exception as e:
        print(f"⚠ student_scores update failed: {e}")

    # Update evaluation_results (most recent entry for this student)
    try:
        db.execute(
            """
            UPDATE evaluation_results
            SET final_score = %s, percentage = %s
            WHERE id = (
                SELECT id FROM evaluation_results
                WHERE submission_id = %s
                ORDER BY evaluated_at DESC
                LIMIT 1
            )
            """,
            [new_score, new_score, student_id],
        )
        updated["evaluation_results"] = True
        print(f"✓ Direct override → evaluation_results: {student_id} = {new_score}")
    except Exception as e:
        print(f"⚠ evaluation_results update failed: {e}")

    if not any(updated.values()):
        raise HTTPException(404, f"No records found for student '{student_id}'")

    return {
        "status": "success",
        "message": f"Score updated to {new_score} for {student_id}",
        "updated": updated,
    }

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
        description="Type of assignment: code, content, mixed, or transcript",
    ),
    problem_statement: Optional[str] = Form(
        None,
        description="Problem statement for code assignments",
    ),
    ideal_reference: Optional[str] = Form(
        None,
        description="Reference content for content assignments",
    ),
    transcript_text: Optional[str] = Form(
        None,
        description="VTT transcript text for transcript summary assignments",
    ),
    rubric_content: Optional[str] = Form(
        None,
        description="Custom rubric as plain text or JSON string (optional)",
    ),
    topic: Optional[str] = Form(
        None,
        description="Topic tag for student progress tracking",
    ),
    test_cases: Optional[str] = Form(
        None,
        description="JSON string of test cases: '[{\"stdin\": \"5\\n3\", \"expected_output\": \"8\"}]'",
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
    - **topic**: Topic tag for student progress tracking (e.g., 'sorting', 'graphs')
    - **test_cases**: JSON string of test cases: '[{"stdin": "5\\n3", "expected_output": "8"}]'
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
    ALLOWED_EXTENSIONS = {".py", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".txt", ".pdf", ".vtt", ".html", ".htm", ".zip"}
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

        # --- ZIP Extraction ---
        # If any ZIP files were uploaded, extract them and discover submissions
        zip_files = list(Path(temp_dir).glob("*.zip"))
        for zf_path in zip_files:
            try:
                with zipfile.ZipFile(str(zf_path), 'r') as zf:
                    # Extract to a subfolder
                    extract_dir = Path(temp_dir) / "_extracted"
                    zf.extractall(str(extract_dir))

                # Walk extracted tree and find submission files
                # Moodle structure: StudentName_ID_assignsubmission_onlinetext/onlinetext.html
                submission_exts = {".html", ".htm", ".txt", ".py", ".cpp", ".pdf"}
                for found_file in extract_dir.rglob("*"):
                    if found_file.is_file() and found_file.suffix.lower() in submission_exts:
                        # Derive student name from parent folder
                        parent_name = found_file.parent.name
                        # Parse Moodle naming: "StudentName_ID_assignsubmission_onlinetext"
                        if "_assignsubmission" in parent_name:
                            student_name = parent_name.split("_assignsubmission")[0]
                            # Clean: "Yashaswini Ramachandra Naik_35463" → keep as-is
                        else:
                            student_name = parent_name

                        # Copy to temp_dir with student name as filename
                        dest_name = f"{student_name}{found_file.suffix.lower()}"
                        dest_path = Path(temp_dir) / dest_name
                        # Avoid overwrites
                        counter = 1
                        while dest_path.exists():
                            dest_name = f"{student_name}_{counter}{found_file.suffix.lower()}"
                            dest_path = Path(temp_dir) / dest_name
                            counter += 1
                        shutil.copy2(str(found_file), str(dest_path))

                # Remove the ZIP and extracted dir
                zf_path.unlink()
                shutil.rmtree(str(extract_dir), ignore_errors=True)
                print(f"✓ Extracted ZIP: found {len(list(Path(temp_dir).iterdir()))} submission files")
            except zipfile.BadZipFile:
                print(f"⚠ Skipping invalid ZIP file: {zf_path.name}")

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

        # Parse test cases if provided as a standalone field
        if test_cases:
            try:
                from backend.app.schemas import TestCase
                tc_list = json.loads(test_cases)
                if not isinstance(tc_list, list):
                    tc_list = [tc_list]
                # Use from_flexible to handle both {stdin,expected_output} and {input,output}
                parsed_test_cases = [TestCase.from_flexible(tc) for tc in tc_list]
                # Filter out empty test cases
                parsed_test_cases = [tc for tc in parsed_test_cases if tc.stdin or tc.expected_output]
                
                if parsed_test_cases:
                    # If no rubric provided, use an empty one to hold test cases
                    if not rubric:
                        rubric = RubricConfig()
                    
                    # Attach parsed test cases to rubric
                    rubric.test_cases = parsed_test_cases
                    print(f"✓ Parsed {len(parsed_test_cases)} test cases")
                else:
                    rubric_warning = "Test cases parsed but none had valid stdin/expected_output."
            except (json.JSONDecodeError, ValueError) as e:
                rubric_warning = f"Failed to parse 'test_cases' JSON: {e}"
                print(rubric_warning)

        # Create evaluation request
        request = EvaluationRequest(
            assignment_type=assignment_type,
            submission_folder=temp_dir,
            problem_statement=problem_statement,
            ideal_reference=ideal_reference,
            transcript_text=transcript_text,
            rubric=rubric,
            topic_tag=topic,
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

        # Persist results to database
        if response.status == "success" and response.results:
            try:
                result_dicts = [r.model_dump() for r in response.results]
                save_evaluation_batch(
                    results=result_dicts,
                    summary=response.summary,
                    csv_output_path=response.csv_output_path,
                    csv_detailed_output_path=response.csv_detailed_output_path,
                )
            except Exception as persist_err:
                print(f"Evaluation persistence failed (non-fatal): {persist_err}")

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


@router.get("/evaluations/history")
def evaluation_history():
    """Retrieve all past evaluation results from the database."""
    data = get_all_evaluations(limit=200)
    return {"status": "success", **data}


@router.delete("/evaluations/cleanup")
def cleanup_evaluations(below_score: float = 10.0):
    """
    Remove evaluation results with scores below a threshold.
    
    Useful for cleaning up broken evaluation results (e.g., old 2.2 scores).
    
    Query params:
    - below_score: Remove results with percentage below this value (default: 10.0)
    """
    from backend.core.services.database import get_db
    
    db = get_db()
    if not db.available:
        raise HTTPException(503, "Database unavailable")
    
    try:
        # Count affected rows first
        count_row = db.execute_one(
            "SELECT COUNT(*) as cnt FROM evaluation_results WHERE percentage < %s",
            [below_score],
        )
        count = count_row["cnt"] if count_row else 0
        
        # Delete the results
        db.execute(
            "DELETE FROM evaluation_results WHERE percentage < %s",
            [below_score],
        )
        
        # Clean up orphaned batches
        db.execute(
            """
            DELETE FROM evaluation_batches
            WHERE batch_id NOT IN (
                SELECT DISTINCT batch_id FROM evaluation_results WHERE batch_id IS NOT NULL
            )
            """
        )
        
        return {
            "status": "success",
            "message": f"Removed {count} evaluation results with score below {below_score}",
            "removed_count": count,
        }
    except Exception as e:
        raise HTTPException(500, f"Cleanup failed: {e}")


@router.delete("/evaluations/clear-all")
def clear_all_evaluations(confirm: bool = False):
    """
    Clear ALL evaluation data from the database.

    Requires confirm=true query parameter to prevent accidental deletion.
    Clears: evaluation_results, student_scores, review_queue, submission_index.
    """
    if not confirm:
        raise HTTPException(
            400,
            "Pass ?confirm=true to confirm deletion of all evaluation data."
        )

    db = get_db()
    if not db.available:
        raise HTTPException(503, "Database unavailable")

    try:
        tables = ["evaluation_results", "student_scores", "review_queue", "submission_index"]
        counts = {}
        for table in tables:
            try:
                # Count first
                result = db.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                counts[table] = result[0]["cnt"] if result else 0
            except Exception:
                counts[table] = 0

            # Always attempt delete
            try:
                db.execute(f"DELETE FROM {table}")
            except Exception as e:
                print(f"⚠ Failed to clear {table}: {e}")

        # Also clean up batches
        try:
            db.execute("DELETE FROM evaluation_batches")
        except Exception:
            pass

        total = sum(counts.values())
        print(f"✓ Cleared all data: {counts}")
        return {
            "status": "success",
            "message": f"Cleared {total} records from database.",
            "details": counts,
        }
    except Exception as e:
        raise HTTPException(500, f"Clear failed: {e}")
