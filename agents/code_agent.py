import ast
from typing import Any, Dict, List

from .base_agent import EvaluationAgent
from utils.llm_service import LLMService


class CodeEvaluationAgent(EvaluationAgent):
    """Evaluates student code submissions through static analysis."""

    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()

    def evaluate(self, input_data: Any) -> Dict[str, Any]:
        """
        Evaluate student code through static analysis.

        Args:
            input_data: Dictionary containing:
                - problem_statement (str): The coding problem
                - rubric (dict): Evaluation criteria with weights
                - student_code (str): The student's code submission

        Returns:
            Dictionary with:
                - score: Total evaluation score
                - max_score: Maximum possible score
                - feedback: List of learning-oriented feedback strings
        """
        problem_statement = input_data.get("problem_statement", "")
        rubric = input_data.get("rubric", {})
        student_code = input_data.get("student_code", "")

        feedback = []
        scores = {}

        # Analyze approach relevance
        approach_score = self._evaluate_approach(
            student_code, problem_statement, feedback
        )
        scores["approach"] = approach_score

        # Analyze readability
        readability_score = self._evaluate_readability(student_code, feedback)
        scores["readability"] = readability_score

        # Analyze structure
        structure_score = self._evaluate_structure(student_code, feedback)
        scores["structure"] = structure_score

        # Analyze visible effort
        effort_score = self._evaluate_effort(student_code, feedback)
        scores["effort"] = effort_score

        # Calculate total score
        weights = rubric.get("weights", {
            "approach": 0.4,
            "readability": 0.2,
            "structure": 0.2,
            "effort": 0.2,
        })

        total_score = sum(scores.get(k, 0) * v for k, v in weights.items())
        max_score = sum(weights.values()) * 100  # Assume each category is out of 100

        # Integrate LLM Feedback (Append-Only)
        if self.llm_service.enabled:
            # Collect deterministic findings for context
            findings = [f for f in feedback if f.startswith("✓") or f.startswith("→")]
            
            llm_feedback = self.llm_service.generate_semantic_feedback(
                "code",
                student_code,
                str(rubric),
                findings
            )
            
            if llm_feedback:
                feedback.append("## AI Tutor Insights")
                feedback.extend(llm_feedback)

        return {
            "score": round(total_score, 2),
            "max_score": max_score,
            "feedback": feedback,
        }

    def _evaluate_approach(
        self, code: str, problem: str, feedback: List[str]
    ) -> float:
        """Evaluate if the approach addresses the problem."""
        score = 50  # Base score

        try:
            tree = ast.parse(code)
        except SyntaxError:
            feedback.append("❌ Code has syntax errors. Review and fix them.")
            return 0

        # Check for functions or classes (indicates problem-solving approach)
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

        if functions or classes:
            score += 30
            feedback.append("✓ Code is organized with functions or classes.")
        else:
            feedback.append("→ Consider organizing code with functions or classes.")

        # Simple keyword matching for problem relevance
        problem_keywords = problem.lower().split()
        code_lower = code.lower()
        keyword_matches = sum(
            1 for keyword in problem_keywords
            if len(keyword) > 3 and keyword in code_lower
        )

        if keyword_matches > 0:
            score += 20
            feedback.append(f"✓ Code addresses problem concepts ({keyword_matches} matches).")
        else:
            feedback.append("→ Ensure your solution directly addresses the problem statement.")

        return min(score, 100)

    def _evaluate_readability(self, code: str, feedback: List[str]) -> float:
        """Evaluate code readability."""
        score = 50

        lines = code.split("\n")
        long_lines = sum(1 for line in lines if len(line.strip()) > 100)

        if long_lines == 0:
            score += 30
            feedback.append("✓ Line length is appropriate for readability.")
        else:
            feedback.append(
                f"→ {long_lines} lines exceed 100 characters. Break them into shorter lines."
            )

        # Check for comments
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        if comment_lines > 0:
            score += 20
            feedback.append(f"✓ Code includes comments ({comment_lines} found).")
        else:
            feedback.append("→ Add comments to explain your logic.")

        return min(score, 100)

    def _evaluate_structure(self, code: str, feedback: List[str]) -> float:
        """Evaluate code structure and organization."""
        score = 50

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0

        # Count functions and classes
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

        total_definitions = len(functions) + len(classes)

        if total_definitions > 2:
            score += 30
            feedback.append(f"✓ Good modularization ({total_definitions} functions/classes).")
        elif total_definitions > 0:
            score += 15
            feedback.append("→ Consider breaking code into more functions for reusability.")

        # Check for meaningful variable names (simple heuristic)
        assignments = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
        ]
        if assignments:
            score += 20
            feedback.append("✓ Code uses variable assignments (structured logic).")

        return min(score, 100)

    def _evaluate_effort(self, code: str, feedback: List[str]) -> float:
        """Evaluate visible effort and complexity."""
        score = 50

        lines = code.split("\n")
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        code_lines = len(non_empty_lines)

        if code_lines > 10:
            score += 30
            feedback.append(f"✓ Substantial code submission ({code_lines} lines).")
        elif code_lines > 5:
            score += 15
            feedback.append("→ Your solution is brief. Consider adding more logic or cases.")
        else:
            feedback.append("→ Your solution is very minimal. Add more implementation.")

        try:
            tree = ast.parse(code)
            # Count control flow statements (loops, conditionals)
            control_flow = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, (ast.If, ast.For, ast.While))
            )
            if control_flow > 0:
                score += 20
                feedback.append(
                    f"✓ Code includes control flow ({control_flow} conditions/loops)."
                )
        except SyntaxError:
            pass

        return min(score, 100)

    # ... existing methods ...

