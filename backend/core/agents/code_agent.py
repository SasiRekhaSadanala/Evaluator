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
        self.STOP_WORDS = {
            "function", "return", "class", "solution", "input", "output", "code", 
            "string", "include", "std", "write", "example", "explanation", "leetcode",
            "implement", "given", "problem", "following", "int", "float", "double", 
            "bool", "void", "vector", "list", "map", "set", "array", "if", "for", 
            "while", "const", "main", "args", "public", "private"
        }
    
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

        language = self._detect_language(student_code, filename)

        feedback = []
        scores = {}

        # Analyze approach relevance
        approach_score = self._evaluate_approach(
            student_code, problem_statement, feedback, language
        )
        scores["approach"] = approach_score

        # 1. Conditional Effort Rewarding (Fixing Grading Inflation)
        # We evaluate approach first, then use it as a gate for other categories.
        
        # Determine Relevance Multiplier
        # Natural Gate: Scale other rewards based on approach relevance
        # If approach is high (>=60), we treat it as fully relevant for effort/structure
        if approach_score >= 60:
            relevance_multiplier = 1.0
        else:
            relevance_multiplier = approach_score / 60.0
        
        # Analyze readability
        readability_raw = self._evaluate_readability(student_code, feedback, language)
        # Readability gets minimal credit (capped at 10%) if irrelevant, otherwise scaled by relevance
        if approach_score == 0:
            scores["readability"] = min(readability_raw, 10)
        else:
            scores["readability"] = readability_raw * relevance_multiplier
        
        # Analyze structure - ONLY rewarded if relevant
        structure_raw = self._evaluate_structure(student_code, feedback, language)
        scores["structure"] = structure_raw * relevance_multiplier
        
        # Analyze visible effort - ONLY rewarded if relevant
        effort_raw = self._evaluate_effort(student_code, feedback, language)
        scores["effort"] = effort_raw * relevance_multiplier

        if approach_score == 0:
            feedback.append("Evaluation Note: Non-relevant submission. Effort and structure rewards are withheld.")

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
                missing_concepts=missing_concepts,
                relevance_status=getattr(self, "_last_relevance_verdict", "UNCERTAIN")
            )
            
            if llm_feedback:
                feedback = ["LLM Explanation:"] + llm_feedback

        return {
            "score": round(total_score, 2),
            "max_score": max_score,
            "feedback": feedback,
        }

    def _evaluate_approach(
        self, code: str, problem: str, feedback: List[str], language: str = "python"
    ) -> float:
        """Evaluate if the approach addresses the problem."""
        
        # Step 1: LLM-based Relevance Check (Primary Gate)
        llm_verdict = None
        if self.llm_service.enabled:
            llm_verdict = self.llm_service.check_relevance(problem, code, "code")
            self._last_relevance_verdict = llm_verdict
            
            # Handle verdicts strictly
            if llm_verdict == "IRRELEVANT":
                feedback.append("⚠️ LLM determined code is irrelevant to the problem. Score: 0.")
                return 0
            elif llm_verdict == "PARTIAL":
                feedback.append("⚠️ LLM found partial relevance. Proceeding with reduced scoring.")
                # Continue to keyword check but cap the score
            elif llm_verdict == "RELEVANT":
                feedback.append("✓ LLM verified submission is relevant to the problem.")
                # Continue to keyword check for final scoring
            elif llm_verdict == "UNCERTAIN":
                # feedback.append("⚠️ LLM could not determine relevance. Falling back to keyword analysis.")
                pass
                # Continue to keyword check as fallback

        score = 0  # Base score removed via previous fix, keeping it 0 here.

        if language == "python":
            return self._evaluate_approach_python(code, problem, feedback, llm_verdict)
        else:  # C++
            return self._evaluate_approach_cpp(code, problem, feedback, llm_verdict)


    
    def _evaluate_approach_python(
        self, code: str, problem: str, feedback: List[str], llm_verdict: str = None
    ) -> float:
        """Evaluate Python code approach using AST."""
        score = 0

        try:
            tree = ast.parse(code)
        except SyntaxError:
            feedback.append("Code has syntax errors. Review and fix them.")
            return 0

        # Simple keyword matching for problem relevance (Fallback/Heuristic)
        problem_keywords = [w for w in set(re.findall(r'\b\w{4,}\b', problem.lower())) if w not in self.STOP_WORDS]
        
        code_lower = code.lower()
        
        covered_keywords = [w for w in problem_keywords if w in code_lower]
        missing_keywords = [w for w in problem_keywords if w not in code_lower]
        
        # Store for LLM use
        self._last_missing_concepts = missing_keywords
        
        keyword_matches = len(covered_keywords)

        # Strict Threshold Calculation
        total_keywords = len(problem_keywords)
        match_ratio = len(covered_keywords) / total_keywords if total_keywords > 0 else 0

        # LLM-based scoring (if LLM gave a verdict)
        if llm_verdict in ["RELEVANT", "PARTIAL"]:
             # LLM confirmed relevance, use keyword match to refine score
             if match_ratio >= 0.3 or len(covered_keywords) >= 3:
                 score = 100 if llm_verdict == "RELEVANT" else 80
                 feedback.append(f"Relevant approach with good keyword alignment.")
             elif match_ratio >= 0.15:
                 score = 90 if llm_verdict == "RELEVANT" else 60
                 feedback.append(f"Relevant approach (LLM verified).")
             else:
                 score = 80 if llm_verdict == "RELEVANT" else 30

                 feedback.append("LLM verified relevance, but keyword match is minimal.")
        
        # Fallback (LLM disabled, uncertain, or failed) - BE STRICT
        else:
            if match_ratio >= 0.25 or len(covered_keywords) >= 2:
                score = 75
                msg = f"Code appears relevant based on keyword match ({len(covered_keywords)} matches)."
                feedback.append(msg)
            else:
                feedback.append(f"Irrelevant submission: Code does not address problem (Low match ratio: {int(match_ratio*100)}%, Found {len(covered_keywords)} keywords).")
                return 0  # Fail-Closed: Irrelevant if not 25%+ match or <3 keywords

        return min(score, 100)

    
    def _evaluate_approach_cpp(
        self, code: str, problem: str, feedback: List[str], llm_verdict: str = None
    ) -> float:
        """Evaluate C++ code approach using regex patterns."""
        score = 0

        # Simple keyword matching for problem relevance (Fallback/Heuristic)
        problem_keywords = [w for w in set(re.findall(r'\b\w{4,}\b', problem.lower())) if w not in self.STOP_WORDS]

        code_lower = code.lower()
        
        covered_keywords = [w for w in problem_keywords if w in code_lower]
        missing_keywords = [w for w in problem_keywords if w not in code_lower]
        
        # Store for LLM use
        self._last_missing_concepts = missing_keywords
        
        keyword_matches = len(covered_keywords)

        # Strict Threshold Calculation
        total_keywords = len(problem_keywords)
        match_ratio = len(covered_keywords) / total_keywords if total_keywords > 0 else 0

        # LLM-based scoring (if LLM gave a verdict)
        if llm_verdict in ["RELEVANT", "PARTIAL"]:
             # LLM confirmed relevance, use keyword match to refine score
             if match_ratio >= 0.3 or len(covered_keywords) >= 3:
                 score = 100 if llm_verdict == "RELEVANT" else 80
                 feedback.append(f"Relevant approach with good keyword alignment.")
             elif match_ratio >= 0.15:
                 score = 90 if llm_verdict == "RELEVANT" else 60
                 feedback.append(f"Relevant approach (LLM verified).")
             else:
                 score = 80 if llm_verdict == "RELEVANT" else 30
                 feedback.append("LLM verified relevance, but keyword match is minimal.")
        else:
            # Fallback (LLM disabled, uncertain, or failed) - Strict
            if match_ratio >= 0.25 or len(covered_keywords) >= 2:
                score = 75
                msg = f"Code appears relevant based on keyword match ({len(covered_keywords)} matches)."
                feedback.append(msg)
            else:
                feedback.append(f"Irrelevant submission: Code does not address problem (Low match ratio: {int(match_ratio*100)}%, Found {len(covered_keywords)} keywords).")
                return 0  # Irrelevant submission

        return min(score, 100)


    def _evaluate_readability(self, code: str, feedback: List[str], language: str = "python") -> float:
        """Evaluate code readability."""
        score = 0

        lines = code.split("\n")
        long_lines = sum(1 for line in lines if len(line.strip()) > 100)

        if long_lines == 0:
            score += 60
            feedback.append("Line length is appropriate for readability.")
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
            score += 40
            feedback.append(f"Code includes comments ({comment_lines} found).")
        else:
            feedback.append("→ Add comments to explain your logic.")

        return min(score, 100)

    def _evaluate_structure(self, code: str, feedback: List[str], language: str = "python") -> float:
        """Evaluate code structure and organization."""
        score = 0

        if language == "python":
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return 0

            # Count functions and classes
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

            total_definitions = len(functions) + len(classes)

            if total_definitions > 0:
                score += 60
                feedback.append(f"Good modularization ({total_definitions} functions/classes).")
            else:
                feedback.append("→ Consider breaking code into functions for reusability.")

            # Check for meaningful variable names (simple heuristic)
            assignments = [
                n for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
            ]
            if assignments:
                score += 40
                feedback.append("Code uses variable assignments (structured logic).")
        else:  # C++
            # Count functions and classes using regex
            function_pattern = r'\w+\s+\w+\s*\([^)]*\)\s*\{'
            functions = re.findall(function_pattern, code)
            
            class_pattern = r'class\s+\w+'
            classes = re.findall(class_pattern, code)
            
            total_definitions = len(functions) + len(classes)
            
            if total_definitions > 0:
                score += 60
                feedback.append(f"Good modularization ({total_definitions} functions/classes).")
            else:
                feedback.append("→ Consider breaking code into functions for reusability.")
            
            # Check for namespace or header guards
            if 'namespace' in code or 'std::' in code or ('#ifndef' in code and '#define' in code):
                score += 40
                feedback.append("✓ Code uses namespaces/guards (good C++ practice).")

        return min(score, 100)

    def _evaluate_effort(self, code: str, feedback: List[str], language: str = "python") -> float:
        """Evaluate visible effort and complexity."""
        score = 0

        lines = code.split("\n")
        # Filter out comments based on language
        if language == "python":
            non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        else:  # C++
            non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("//")]
        
        code_lines = len(non_empty_lines)

        if code_lines > 5:
            score += 60
            feedback.append("Substantial code submission" + f" ({code_lines} lines).")
        elif code_lines > 0:
            score += 30
            feedback.append("→ Your solution is brief. Consider adding more logic or cases.")

        # Count control flow statements
        if language == "python":
            try:
                tree = ast.parse(code)
                control_flow = sum(
                    1 for n in ast.walk(tree)
                    if isinstance(n, (ast.If, ast.For, ast.While))
                )
                if control_flow > 0:
                    score += 40
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
