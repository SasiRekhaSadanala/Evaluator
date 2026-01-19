import ast
import re
from typing import Any, Dict, List

from .base_agent import EvaluationAgent
from utils.llm_service import LLMService


class CodeEvaluationAgent(EvaluationAgent):
    """Evaluates student code submissions through static analysis."""

    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
    
    def _detect_language(self, code: str, filename: str = "") -> str:
        """Detect programming language from code or filename."""
        if filename:
            ext = filename.lower().split('.')[-1] if '.' in filename else ""
            if ext in ['cpp', 'cc', 'cxx', 'h', 'hpp']:
                return 'cpp'
            elif ext == 'py':
                return 'python'
        
        # Fallback: check code patterns
        if '#include' in code or 'std::' in code:
            return 'cpp'
        return 'python'

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
        filename = input_data.get("filename", "")

        # Detect language
        language = self._detect_language(student_code, filename)

        feedback = []
        scores = {}

        # Analyze approach relevance
        approach_score = self._evaluate_approach(
            student_code, problem_statement, feedback, language
        )
        scores["approach"] = approach_score

        # Analyze readability
        readability_score = self._evaluate_readability(student_code, feedback, language)
        scores["readability"] = readability_score

        # Analyze structure
        structure_score = self._evaluate_structure(student_code, feedback, language)
        scores["structure"] = structure_score

        # Analyze visible effort
        effort_score = self._evaluate_effort(student_code, feedback, language)
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

        # Integrate LLM Feedback (Step 2, 4, 5)
        if self.llm_service.enabled:
            # Collect missing concepts for semantic explanation (Step 4)
            missing_concepts = getattr(self, "_last_missing_concepts", [])
            
            # Collect deterministic findings for context
            findings = [f for f in feedback if f.startswith("✓") or f.startswith("→") or f.startswith("❌")]
            
            llm_feedback = self.llm_service.generate_semantic_feedback(
                context_type="code",
                submission_content=student_code,
                rubric_context=str(rubric),
                deterministic_findings=findings,
                missing_concepts=missing_concepts
            )
            
            if llm_feedback:
                feedback.append("LLM Explanation:")  # Step 5
                feedback.extend(llm_feedback)

        return {
            "score": round(total_score, 2),
            "max_score": max_score,
            "feedback": feedback,
        }

    def _evaluate_approach(
        self, code: str, problem: str, feedback: List[str], language: str = "python"
    ) -> float:
        """Evaluate if the approach addresses the problem."""
        score = 50  # Base score

        if language == "python":
            return self._evaluate_approach_python(code, problem, feedback)
        else:  # C++
            return self._evaluate_approach_cpp(code, problem, feedback)
    
    def _evaluate_approach_python(
        self, code: str, problem: str, feedback: List[str]
    ) -> float:
        """Evaluate Python code approach using AST."""
        score = 50

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
        problem_keywords = [w for w in problem.lower().split() if len(w) > 3]
        code_lower = code.lower()
        
        covered_keywords = [w for w in problem_keywords if w in code_lower]
        missing_keywords = [w for w in problem_keywords if w not in code_lower]
        
        # Store for LLM use
        self._last_missing_concepts = missing_keywords
        
        keyword_matches = len(covered_keywords)

        if keyword_matches > 0:
            score += 20
            msg = f"✓ Code addresses problem concepts ({keyword_matches} matches)."
            if missing_keywords and not self.llm_service.enabled:
                msg += f" Missing: {', '.join(missing_keywords[:3])}"
            feedback.append(msg)
        else:
            feedback.append("→ Ensure your solution directly addresses the problem statement.")

        return min(score, 100)
    
    def _evaluate_approach_cpp(
        self, code: str, problem: str, feedback: List[str]
    ) -> float:
        """Evaluate C++ code approach using regex patterns."""
        score = 50

        # Check for functions (basic pattern)
        function_pattern = r'\w+\s+\w+\s*\([^)]*\)\s*\{'
        functions = re.findall(function_pattern, code)
        
        # Check for classes
        class_pattern = r'class\s+\w+'
        classes = re.findall(class_pattern, code)
        
        if functions or classes:
            score += 30
            feedback.append(f"✓ Code is organized with {len(functions)} function(s) and {len(classes)} class(es).")
        else:
            feedback.append("→ Consider organizing code with functions or classes.")
        
        # Check for includes (shows awareness of libraries)
        include_pattern = r'#include\s*[<"][^>"]+[>"]'
        includes = re.findall(include_pattern, code)
        if includes:
            score += 10
            feedback.append(f"✓ Code includes {len(includes)} header file(s).")
        
        # Simple keyword matching for problem relevance
        problem_keywords = [w for w in problem.lower().split() if len(w) > 3]
        code_lower = code.lower()
        
        covered_keywords = [w for w in problem_keywords if w in code_lower]
        missing_keywords = [w for w in problem_keywords if w not in code_lower]
        
        # Store for LLM use
        self._last_missing_concepts = missing_keywords
        
        keyword_matches = len(covered_keywords)

        if keyword_matches > 0:
            score += 10
            msg = f"✓ Code addresses problem concepts ({keyword_matches} matches)."
            if missing_keywords and not self.llm_service.enabled:
                msg += f" Missing: {', '.join(missing_keywords[:3])}"
            feedback.append(msg)
        else:
            feedback.append("→ Ensure your solution directly addresses the problem statement.")

        return min(score, 100)

    def _evaluate_readability(self, code: str, feedback: List[str], language: str = "python") -> float:
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

        # Check for comments (language-specific)
        if language == "python":
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        else:  # C++
            # Count both // and /* */ style comments
            single_line_comments = sum(1 for line in lines if "//" in line)
            multi_line_comments = len(re.findall(r'/\*.*?\*/', code, re.DOTALL))
            comment_lines = single_line_comments + multi_line_comments
        
        if comment_lines > 0:
            score += 20
            feedback.append(f"✓ Code includes comments ({comment_lines} found).")
        else:
            feedback.append("→ Add comments to explain your logic.")

        return min(score, 100)

    def _evaluate_structure(self, code: str, feedback: List[str], language: str = "python") -> float:
        """Evaluate code structure and organization."""
        score = 50

        if language == "python":
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
        else:  # C++
            # Count functions and classes using regex
            function_pattern = r'\w+\s+\w+\s*\([^)]*\)\s*\{'
            functions = re.findall(function_pattern, code)
            
            class_pattern = r'class\s+\w+'
            classes = re.findall(class_pattern, code)
            
            total_definitions = len(functions) + len(classes)
            
            if total_definitions > 2:
                score += 30
                feedback.append(f"✓ Good modularization ({total_definitions} functions/classes).")
            elif total_definitions > 0:
                score += 15
                feedback.append("→ Consider breaking code into more functions for reusability.")
            
            # Check for namespace usage
            if 'namespace' in code or 'std::' in code:
                score += 10
                feedback.append("✓ Code uses namespaces (good C++ practice).")
            
            # Check for header guards (in .h files)
            if '#ifndef' in code and '#define' in code:
                score += 10
                feedback.append("✓ Header guards detected (good practice).")

        return min(score, 100)

    def _evaluate_effort(self, code: str, feedback: List[str], language: str = "python") -> float:
        """Evaluate visible effort and complexity."""
        score = 50

        lines = code.split("\n")
        # Filter out comments based on language
        if language == "python":
            non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        else:  # C++
            non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("//")]
        
        code_lines = len(non_empty_lines)

        if code_lines > 10:
            score += 30
            feedback.append(f"✓ Substantial code submission ({code_lines} lines).")
        elif code_lines > 5:
            score += 15
            feedback.append("→ Your solution is brief. Consider adding more logic or cases.")
        else:
            feedback.append("→ Your solution is very minimal. Add more implementation.")

        # Count control flow statements
        if language == "python":
            try:
                tree = ast.parse(code)
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
        else:  # C++
            # Count if, for, while, switch statements
            control_patterns = [
                r'\bif\s*\(',
                r'\bfor\s*\(',
                r'\bwhile\s*\(',
                r'\bswitch\s*\('
            ]
            control_flow = sum(len(re.findall(pattern, code)) for pattern in control_patterns)
            if control_flow > 0:
                score += 20
                feedback.append(
                    f"✓ Code includes control flow ({control_flow} conditions/loops)."
                )

        return min(score, 100)
