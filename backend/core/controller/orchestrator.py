from typing import Any, Dict, List, Optional

from ..agents.aggregator_agent import AggregatorAgent
from ..agents.code_agent import CodeEvaluationAgent
from ..agents.content_agent import ContentEvaluationAgent
from ..utils.file_parser import (
    get_student_name_from_filename,
    read_folder,
    read_submissions_by_type,
)
from ..utils.rubric import Rubric


class Orchestrator:
    """Orchestrates evaluation workflow across student submissions."""

    ASSIGNMENT_TYPES = {"code", "content", "mixed"}

    def __init__(self, rubric: Optional[Rubric] = None):
        """
        Initialize orchestrator with optional rubric.

        Args:
            rubric: Rubric instance. If None, uses default rubric.
        """
        self.rubric = rubric or Rubric()
        self.code_agent = CodeEvaluationAgent()
        self.content_agent = ContentEvaluationAgent()
        self.aggregator_agent = AggregatorAgent()

    def evaluate_submissions(
        self,
        assignment_type: str,
        folder_path: str,
        problem_statement: Optional[str] = None,
        ideal_reference: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate all submissions in a folder.

        Args:
            assignment_type: Type of assignment ('code', 'content', or 'mixed')
            folder_path: Path to folder containing student submissions
            problem_statement: For code assignments, the problem statement
            ideal_reference: For content assignments, reference content

        Returns:
            Dictionary mapping student names to final evaluation results
        """
        if assignment_type not in self.ASSIGNMENT_TYPES:
            raise ValueError(
                f"Invalid assignment type. Must be one of: {self.ASSIGNMENT_TYPES}"
            )

        # Read submissions
        if assignment_type == "mixed":
            submissions = read_submissions_by_type(folder_path)
        else:
            submissions = read_folder(folder_path)

        # Evaluate each submission
        results = {}

        if assignment_type == "code":
            results = self._evaluate_code_submissions(
                submissions, problem_statement
            )
        elif assignment_type == "content":
            results = self._evaluate_content_submissions(
                submissions, ideal_reference, problem_statement
            )
        elif assignment_type == "mixed":
            results = self._evaluate_mixed_submissions(
                submissions, problem_statement, ideal_reference
            )

        return results

    def _evaluate_code_submissions(
        self,
        submissions: Dict[str, str],
        problem_statement: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate code-only submissions.

        Args:
            submissions: Dict of filename to code content
            problem_statement: Problem description for context

        Returns:
            Results mapped to student names
        """
        results = {}

        for filename, code in submissions.items():
            student_name = get_student_name_from_filename(filename)

            # Prepare input for code agent
            code_criteria = self.rubric.get_criteria("code")
            code_weights = {k: v.get("weight", 0.25) for k, v in code_criteria.items()}
            agent_input = {
                "problem_statement": problem_statement or "",
                "rubric": {"weights": code_weights},
                "student_code": code,
                "filename": filename,  # Add filename for language detection
            }

            # Evaluate with code agent
            code_output = self.code_agent.evaluate(agent_input)

            # Aggregate (single agent, so just pass through)
            aggregator_input = {
                "agent_outputs": [code_output],
                "rubric": {"weights": [1.0]},
            }
            final_result = self.aggregator_agent.evaluate(aggregator_input)

            results[student_name] = {
                "file": filename,
                "assignment_type": "code",
                **final_result,
            }

        return results

    def _evaluate_content_submissions(
        self,
        submissions: Dict[str, str],
        ideal_reference: Optional[str] = None,
        problem_statement: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate content-only submissions.

        Args:
            submissions: Dict of filename to content
            ideal_reference: Reference content for comparison
            problem_statement: Problem description for concept extraction

        Returns:
            Results mapped to student names
        """
        results = {}

        for filename, content in submissions.items():
            student_name = get_student_name_from_filename(filename)

            # Prepare input for content agent
            content_criteria = self.rubric.get_criteria("content")
            content_weights = {k: v.get("weight", 0.25) for k, v in content_criteria.items()}
            agent_input = {
                "student_content": content,
                "rubric": {"weights": content_weights},
                "ideal_reference": ideal_reference or "",
                "problem_statement": problem_statement or "",  # NEW: for auto-extraction
            }

            # Evaluate with content agent
            content_output = self.content_agent.evaluate(agent_input)

            # Aggregate (single agent, so just pass through)
            aggregator_input = {
                "agent_outputs": [content_output],
                "rubric": {"weights": [1.0]},
            }
            final_result = self.aggregator_agent.evaluate(aggregator_input)

            results[student_name] = {
                "file": filename,
                "assignment_type": "content",
                **final_result,
            }

        return results

    def _evaluate_mixed_submissions(
        self,
        submissions: Dict[str, Dict[str, str]],
        problem_statement: Optional[str] = None,
        ideal_reference: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate mixed submissions (both code and content).

        Args:
            submissions: Dict with 'code' and 'text' keys containing submissions
            problem_statement: Problem description for code context
            ideal_reference: Reference content for content comparison

        Returns:
            Results mapped to student names
        """
        results = {}

        # Get all unique students across code and content submissions
        code_submissions = submissions.get("code", {})
        content_submissions = submissions.get("text", {})

        all_students = set(
            get_student_name_from_filename(f)
            for f in list(code_submissions.keys()) + list(content_submissions.keys())
        )

        for student_name in all_students:
            agent_outputs = []

            # Evaluate code if available
            for filename, code in code_submissions.items():
                if get_student_name_from_filename(filename) == student_name:
                    code_criteria = self.rubric.get_criteria("code")
                    code_weights = {k: v.get("weight", 0.25) for k, v in code_criteria.items()}
                    agent_input = {
                        "problem_statement": problem_statement or "",
                        "rubric": {"weights": code_weights},
                        "student_code": code,
                        "filename": filename,  # Add filename for language detection
                    }
                    code_output = self.code_agent.evaluate(agent_input)
                    agent_outputs.append(code_output)
                    break

            # Evaluate content if available
            for filename, content in content_submissions.items():
                if get_student_name_from_filename(filename) == student_name:
                    content_criteria = self.rubric.get_criteria("content")
                    content_weights = {k: v.get("weight", 0.25) for k, v in content_criteria.items()}
                    agent_input = {
                        "student_content": content,
                        "rubric": {"weights": content_weights},
                        "ideal_reference": ideal_reference or "",
                        "problem_statement": problem_statement or "",  # NEW: for auto-extraction
                    }
                    content_output = self.content_agent.evaluate(agent_input)
                    agent_outputs.append(content_output)
                    break

            # Aggregate results
            if agent_outputs:
                weights = self.rubric.get_weights()
                aggregator_input = {
                    "agent_outputs": agent_outputs,
                    "rubric": {"weights": list(weights.values())},
                }
                final_result = self.aggregator_agent.evaluate(aggregator_input)

                results[student_name] = {
                    "assignment_type": "mixed",
                    "agent_count": len(agent_outputs),
                    **final_result,
                }

        return results

    def get_rubric(self) -> Rubric:
        """
        Get the rubric used by this orchestrator.

        Returns:
            Rubric instance
        """
        return self.rubric

    def set_rubric(self, rubric: Rubric) -> None:
        """
        Set a new rubric for evaluation.

        Args:
            rubric: New Rubric instance
        """
        self.rubric = rubric
