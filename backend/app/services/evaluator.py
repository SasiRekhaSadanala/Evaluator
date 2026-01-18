"""Service layer for evaluation API."""

from typing import Any, Dict, List, Optional

from backend.app.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResultItem,
    RubricConfig,
)
from backend.core.controller.orchestrator import Orchestrator
from backend.core.utils.csv_export import (
    export_results_to_csv,
    export_results_to_detailed_csv,
)
from backend.core.utils.rubric import Rubric


class EvaluatorService:
    """Service layer adapting API requests to orchestrator."""

    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Evaluate submissions based on API request.

        Converts API request to orchestrator format, runs evaluation,
        and converts results back to API response format.

        Args:
            request: EvaluationRequest with assignment details

        Returns:
            EvaluationResponse with results and CSV paths
        """
        try:
            # Create rubric from request or use default
            rubric = self._create_rubric(request.rubric)

            # Create orchestrator
            orchestrator = Orchestrator(rubric=rubric)

            # Evaluate submissions
            raw_results = orchestrator.evaluate_submissions(
                assignment_type=request.assignment_type,
                folder_path=request.submission_folder,
                problem_statement=request.problem_statement,
                ideal_reference=request.ideal_reference,
            )

            # Convert results
            formatted_results = self._format_results(raw_results)
            summary = self._calculate_summary(formatted_results)

            # Export to CSV
            csv_path = self._export_csv(raw_results)
            csv_detailed_path = self._export_csv_detailed(raw_results)

            return EvaluationResponse(
                status="success",
                message=f"Evaluated {len(formatted_results)} submissions successfully",
                results=formatted_results,
                summary=summary,
                csv_output_path=csv_path,
                csv_detailed_output_path=csv_detailed_path,
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in EvaluatorService.evaluate:")
            print(f"  Exception type: {type(e).__name__}")
            print(f"  Exception message: {str(e)}")
            print(f"  Traceback:\n{error_details}")
            return EvaluationResponse(
                status="error",
                message="Evaluation failed",
                error_message=str(e),
            )

    def _create_rubric(
        self, rubric_config: Optional[RubricConfig]
    ) -> Optional[Rubric]:
        """
        Convert API rubric config to Rubric object.

        Args:
            rubric_config: RubricConfig from API request

        Returns:
            Rubric instance or None to use default
        """
        if rubric_config is None:
            return None

        # Convert to dict format expected by Rubric
        rubric_dict = {
            "name": rubric_config.name or "Standard Rubric",
            "version": rubric_config.version or "1.0",
        }

        if rubric_config.dimensions:
            rubric_dict["dimensions"] = {
                k: (v.model_dump() if hasattr(v, "model_dump") else v)
                for k, v in rubric_config.dimensions.items()
            }

        return Rubric(rubric_dict)

    def _format_results(
        self, raw_results: Dict[str, Dict[str, Any]]
    ) -> List[EvaluationResultItem]:
        """
        Convert orchestrator output to API response format.

        Args:
            raw_results: Results from orchestrator.evaluate_submissions()

        Returns:
            List of EvaluationResultItem for API response
        """
        formatted = []

        for student_name, result in raw_results.items():
            final_score = result.get("final_score", 0)
            max_score = result.get("max_score", 100)
            percentage = (
                (final_score / max_score * 100) if max_score > 0 else 0
            )

            # Extract feedback - handle both list and combined_feedback formats
            feedback = result.get("combined_feedback", [])
            if isinstance(feedback, str):
                feedback = [feedback]

            item = EvaluationResultItem(
                submission_id=student_name,
                final_score=final_score,
                max_score=max_score,
                percentage=round(percentage, 2),
                feedback=feedback or [],
                assignment_type=result.get("assignment_type", "unknown"),
                file=result.get("file", ""),
            )
            formatted.append(item)

        return formatted

    def _calculate_summary(
        self, results: List[EvaluationResultItem]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate summary statistics.

        Args:
            results: List of formatted evaluation results

        Returns:
            Dictionary with aggregate statistics
        """
        if not results:
            return None

        scores = [r.final_score for r in results]
        percentages = [r.percentage for r in results]

        return {
            "total_submissions": len(results),
            "average_score": round(sum(scores) / len(scores), 2),
            "average_percentage": round(sum(percentages) / len(percentages), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
        }

    def _export_csv(
        self, raw_results: Dict[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Export results to summary CSV.

        Args:
            raw_results: Results from orchestrator

        Returns:
            Path to CSV file or None if export failed
        """
        try:
            path = export_results_to_csv(raw_results)
            return path
        except Exception:
            return None

    def _export_csv_detailed(
        self, raw_results: Dict[str, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Export results to detailed CSV.

        Args:
            raw_results: Results from orchestrator

        Returns:
            Path to detailed CSV file or None if export failed
        """
        try:
            path = export_results_to_detailed_csv(raw_results)
            return path
        except Exception:
            return None
