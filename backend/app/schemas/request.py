"""Request/Response schemas for evaluation API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """A single test case for code execution.
    
    Accepts both formats:
      - {"stdin": "...", "expected_output": "..."}
      - {"input": "...", "output": "..."}
    """

    stdin: str = Field(default="", description="Standard input for the test case")
    expected_output: str = Field(default="", description="Expected standard output")

    @classmethod
    def from_flexible(cls, data: dict) -> "TestCase":
        """Create TestCase from dict with flexible key names."""
        stdin = data.get("stdin") or data.get("input") or ""
        expected_output = data.get("expected_output") or data.get("output") or ""
        # Handle case where input/output are non-string (e.g., lists, ints)
        if not isinstance(stdin, str):
            stdin = str(stdin)
        if not isinstance(expected_output, str):
            expected_output = str(expected_output)
        return cls(stdin=stdin, expected_output=expected_output)


class RubricDimension(BaseModel):
    """Rubric dimension configuration."""

    weight: float = Field(..., ge=0, le=1, description="Weight for this dimension")
    max_score: float = Field(..., gt=0, description="Maximum score for this dimension")
    criteria: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None, description="Evaluation criteria for this dimension"
    )


class RubricConfig(BaseModel):
    """Rubric configuration for evaluation."""

    name: Optional[str] = Field(default="Standard Rubric", description="Rubric name")
    version: Optional[str] = Field(default="1.0", description="Rubric version")
    dimensions: Optional[Dict[str, RubricDimension]] = Field(
        default=None,
        description="Dimensions with code and content weights.",
    )
    test_cases: Optional[List[TestCase]] = Field(
        default=None,
        description="Test cases for code execution via Judge0.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Standard Rubric",
                "version": "1.0",
                "dimensions": {
                    "code": {
                        "weight": 0.6,
                        "max_score": 100,
                        "criteria": {
                            "approach": {"weight": 0.4, "max_score": 100},
                            "readability": {"weight": 0.2, "max_score": 100},
                            "structure": {"weight": 0.2, "max_score": 100},
                            "effort": {"weight": 0.2, "max_score": 100},
                        },
                    },
                    "content": {
                        "weight": 0.4,
                        "max_score": 100,
                        "criteria": {
                            "coverage": {"weight": 0.35, "max_score": 100},
                            "alignment": {"weight": 0.25, "max_score": 100},
                            "flow": {"weight": 0.2, "max_score": 100},
                            "completeness": {"weight": 0.2, "max_score": 100},
                        },
                    },
                },
            }
        }


class EvaluationRequest(BaseModel):
    """Request schema for evaluation API."""

    assignment_type: str = Field(
        ...,
        description="Type of assignment: 'code', 'content', 'mixed', or 'transcript'",
        pattern="^(code|content|mixed|transcript)$",
    )
    submission_folder: str = Field(
        ..., description="Path to folder containing student submissions"
    )
    problem_statement: Optional[str] = Field(
        default=None, description="Problem statement (for code assignments)"
    )
    ideal_reference: Optional[str] = Field(
        default=None, description="Reference content (for content assignments)"
    )
    transcript_text: Optional[str] = Field(
        default=None, description="VTT transcript text (for transcript summary assignments)"
    )
    rubric: Optional[RubricConfig] = Field(
        default=None,
        description="Custom rubric configuration. If not provided, uses default rubric.",
    )
    topic_tag: Optional[str] = Field(
        default=None,
        description="Topic tag for student progress tracking (e.g., 'sorting', 'graphs').",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "assignment_type": "code",
                "submission_folder": "./submissions",
                "problem_statement": "Write a function to calculate factorial",
                "rubric": None,
            }
        }


class EvaluationResultItem(BaseModel):
    """Individual evaluation result for a student."""

    submission_id: str = Field(..., description="Student identifier")
    final_score: float = Field(..., ge=0, description="Final numeric score")
    max_score: float = Field(..., gt=0, description="Maximum possible score")
    percentage: float = Field(..., ge=0, le=100, description="Score as percentage")
    feedback: List[str] = Field(..., description="List of feedback items")
    assignment_type: str = Field(..., description="Type of assignment evaluated")
    file: str = Field(..., description="Submission filename")
    # --- Integrity fields (Feature 4) ---
    flag_score: Optional[float] = Field(
        default=None,
        description="Integrity flag score (0–1). >0.7 triggers review queue.",
    )
    flag_reasons: Optional[List[str]] = Field(
        default=None,
        description="Reasons for integrity flag.",
    )
    # --- Student profile fields (Feature 6) ---
    percentile: Optional[int] = Field(
        default=None,
        description="Percentile rank within class (0–100).",
    )
    improvement_delta: Optional[float] = Field(
        default=None,
        description="Score change vs student's recent average.",
    )
    trend: Optional[str] = Field(
        default=None,
        description="Performance trend: 'improving', 'stable', or 'declining'.",
    )


class EvaluationResponse(BaseModel):
    """Response schema for evaluation API."""

    status: str = Field(..., description="Status of evaluation: 'success' or 'error'")
    message: str = Field(..., description="Status message")
    results: Optional[List[EvaluationResultItem]] = Field(
        default=None, description="List of evaluation results for each student"
    )
    summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Summary statistics (count, average score, etc.)",
    )
    csv_output_path: Optional[str] = Field(
        default=None, description="Path to generated CSV results file"
    )
    csv_detailed_output_path: Optional[str] = Field(
        default=None, description="Path to generated detailed CSV results file"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error details if status is 'error'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Evaluated 3 submissions successfully",
                "results": [
                    {
                        "submission_id": "john_doe_submission_Result",
                        "final_score": 92.5,
                        "max_score": 100,
                        "percentage": 92.5,
                        "feedback": [
                            "Good code structure",
                            "Consider adding more comments",
                        ],
                        "assignment_type": "code",
                        "file": "john_doe_submission.py",
                    }
                ],
                "summary": {
                    "total_submissions": 3,
                    "average_score": 91.67,
                    "highest_score": 97,
                    "lowest_score": 85,
                },
                "csv_output_path": "./outputs/results.csv",
                "csv_detailed_output_path": "./outputs/results_detailed.csv",
            }
        }


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    version: str = Field(..., description="API version")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "message": "API is running",
            }
        }
