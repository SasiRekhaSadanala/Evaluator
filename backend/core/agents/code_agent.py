"""
Code Evaluation Agent — v2.1

Evaluates student code submissions through:
- Tree-sitter AST analysis (unified across Python & C++)
- Judge0 test case execution (when test cases are available)
- LLM relevance verification
- AST-aware function name matching + complexity scoring (improved fallback)
- Keyword heuristics (last resort)

v2.1 changes:
- UNCERTAIN LLM verdicts no longer penalize scores
- Keyword matching replaced with AST-aware differentiation
- complexity_score from tree-sitter used to differentiate similar code
"""

import re
from typing import Any, Dict, List, Optional

from .base_agent import EvaluationAgent
from utils.llm_service import LLMService
from backend.core.services.treesitter_parser import extract_features


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
            "while", "const", "main", "args", "public", "private", "self", "none",
            "true", "false", "print", "range", "nums", "that", "with", "from",
            "this", "which", "each", "such", "your", "have", "will", "than",
            "should", "would", "could", "does", "more", "need", "also", "only",
        }
        self._judge0_service = None  # Lazy-loaded

    def _get_judge0(self):
        """Lazy-load Judge0 service."""
        if self._judge0_service is None:
            try:
                from backend.core.services.judge0_service import Judge0Service
                self._judge0_service = Judge0Service()
            except Exception:
                self._judge0_service = False  # Mark as unavailable
        return self._judge0_service if self._judge0_service is not False else None

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
        Evaluate student code through static analysis + optional test execution.

        Args:
            input_data: Dictionary containing:
                - problem_statement (str): The coding problem
                - rubric (dict): Evaluation criteria with weights
                - student_code (str): The student's code submission
                - filename (str): Original filename for language detection
                - test_cases (list, optional): [{stdin, expected_output}, ...]

        Returns:
            Dictionary with score, max_score, feedback
        """
        problem_statement = input_data.get("problem_statement", "")
        rubric = input_data.get("rubric", {})
        student_code = input_data.get("student_code", "")
        filename = input_data.get("filename", "")
        test_cases = input_data.get("test_cases", [])

        language = self._detect_language(student_code, filename)

        # ── Parse code once via tree-sitter (used by all scoring methods) ──
        features = extract_features(student_code, language)

        # Immediate fail if syntax error detected
        if features.get("has_syntax_error"):
            return {
                "score": 0,
                "max_score": 100,
                "feedback": [
                    "❌ Code has syntax errors and cannot be parsed.",
                    f"→ Parser mode: {features.get('parser_mode', 'unknown')}",
                    "→ Fix syntax errors before resubmitting.",
                ],
            }

        feedback = []
        scores = {}

        # ── Check if problem statement is meaningful ──
        has_problem = bool(problem_statement and problem_statement.strip())

        # ── Approach scoring ──
        # Use test_cases from rubric if available, otherwise keep the ones from input_data
        rubric_tests = rubric.get("test_cases", [])
        if rubric_tests:
            test_cases = rubric_tests
        if has_problem:
            approach_score = self._evaluate_approach(
                student_code, problem_statement, feedback, language, test_cases, features
            )
        else:
            # No problem statement — grade purely on code quality
            complexity = features.get("complexity_score", 50)
            approach_score = min(60 + (complexity * 0.3), 90)
            feedback.append(
                "ℹ No problem statement provided. Evaluating code quality only."
            )
            self._last_relevance_verdict = "RELEVANT"
            self._last_missing_concepts = []
        scores["approach"] = approach_score

        # Capture test pass rate for score floor calculation later
        test_pass_rate = getattr(self, "_last_test_pass_rate", None)

        # ── Conditional Effort Rewarding (relevance gate) ──
        # CRITICAL FIX: Only apply penalty when LLM EXPLICITLY says IRRELEVANT.
        # UNCERTAIN means "LLM couldn't determine" — NOT "code is bad".
        verdict = getattr(self, "_last_relevance_verdict", "UNCERTAIN")
        if verdict == "IRRELEVANT":
            # LLM explicitly confirmed irrelevance — apply very strong penalty
            # Wrong-problem submissions should not earn effort/structure credit
            relevance_multiplier = 0.1
        elif verdict == "PARTIAL":
            # LLM says partially relevant — moderate penalty
            relevance_multiplier = 0.5
        else:
            # RELEVANT or UNCERTAIN — no penalty
            relevance_multiplier = 1.0

        # ── Readability ──
        readability_raw = self._evaluate_readability(student_code, feedback, language)
        scores["readability"] = readability_raw * relevance_multiplier

        # ── Structure (uses unified features dict) ──
        structure_raw = self._evaluate_structure(student_code, feedback, language, features)
        scores["structure"] = structure_raw * relevance_multiplier

        # ── Effort (uses unified features dict) ──
        effort_raw = self._evaluate_effort(student_code, feedback, language, features)
        scores["effort"] = effort_raw * relevance_multiplier

        if verdict == "IRRELEVANT":
            feedback.append(
                "⚠️ Wrong problem submitted. Code quality rewards are heavily reduced. "
                "Please solve the assigned problem."
            )

        # ── Calculate total score ──
        weights = rubric.get("weights", {
            "approach": 0.4,
            "readability": 0.2,
            "structure": 0.2,
            "effort": 0.2,
        })

        total_score = sum(scores.get(k, 0) * v for k, v in weights.items())
        max_score = 100  # Always out of 100

        # ── Test pass rate floor ──
        # When test cases run and pass at a high rate, this is the strongest
        # objective signal. Don't let readability/structure drag below this.
        if test_pass_rate is not None and test_pass_rate >= 50:
            # Floor = 95% of test pass rate (so 80% pass → floor of 76)
            test_floor = test_pass_rate * 0.95
            if total_score < test_floor:
                feedback.append(
                    f"✓ Score boosted by test results: {total_score:.1f} → {test_floor:.1f} "
                    f"(test pass rate: {test_pass_rate:.0f}%)"
                )
                total_score = test_floor

        # ── Hard cap for IRRELEVANT submissions ──
        # Even if readability/structure/effort are perfect, wrong-problem
        # submissions should never score above 25.
        if verdict == "IRRELEVANT":
            total_score = min(total_score, 25)

        # ── LLM Feedback ──
        if self.llm_service.enabled:
            missing_concepts = getattr(self, "_last_missing_concepts", [])
            findings = [
                f for f in feedback
                if f.startswith("✓") or f.startswith("→") or f.startswith("❌")
            ]
            llm_feedback = self.llm_service.generate_semantic_feedback(
                context_type="code",
                submission_content=student_code,
                rubric_context=str(rubric),
                deterministic_findings=findings,
                missing_concepts=missing_concepts,
                relevance_status=getattr(self, "_last_relevance_verdict", "UNCERTAIN"),
            )
            if llm_feedback:
                feedback = ["LLM Explanation:"] + llm_feedback

        return {
            "score": round(min(total_score, 100), 2),
            "max_score": max_score,
            "feedback": feedback,
        }

    # ======================================================================
    # APPROACH — v2.1 with AST-aware scoring
    # ======================================================================

    def _evaluate_approach(
        self,
        code: str,
        problem: str,
        feedback: List[str],
        language: str,
        test_cases: List[dict] = None,
        features: Dict = None,
    ) -> float:
        """
        Evaluate if the approach addresses the problem.

        v2.1 Scoring strategy:
        - If test_cases exist → approach = 0.4 * relevance + 0.6 * test_score
        - If no test_cases   → AST-aware function matching + keyword + complexity
        """
        test_cases = test_cases or []
        features = features or extract_features(code, language)

        # ── Step 1: LLM-based relevance check ──
        llm_verdict = None
        if self.llm_service.enabled:
            llm_verdict = self.llm_service.check_relevance(problem, code, "code")
            self._last_relevance_verdict = llm_verdict

            if llm_verdict == "IRRELEVANT":
                feedback.append(
                    "⚠️ LLM determined code is irrelevant to the problem. Score: 0."
                )
                return 0
            elif llm_verdict == "PARTIAL":
                feedback.append(
                    "⚠️ LLM found partial relevance. Proceeding with reduced scoring."
                )
            elif llm_verdict == "RELEVANT":
                feedback.append(
                    "✓ LLM verified submission is relevant to the problem."
                )
            # UNCERTAIN falls through to AST + keyword logic
        else:
            self._last_relevance_verdict = "UNCERTAIN"

        # ── Step 2: AST-aware function name matching ──
        function_names = features.get("function_names", [])
        fn_match_score = self._function_name_relevance(function_names, problem, feedback)

        # ── Step 3: Keyword relevance (improved) ──
        keyword_score = self._keyword_relevance_score(code, problem, feedback, llm_verdict)

        # ── Step 4: Complexity bonus ──
        complexity = features.get("complexity_score", 30)
        # Normalize complexity to 0-100 scale (it's already 0-100)
        complexity_bonus = min(complexity * 0.15, 15)  # Up to 15 bonus points

        # ── Step 5: Combine approach components ──
        if llm_verdict in ("RELEVANT", "PARTIAL"):
            # LLM gave an explicit verdict — trust it more
            if llm_verdict == "RELEVANT":
                base_score = max(keyword_score, fn_match_score, 85)
            else:
                base_score = max(keyword_score, fn_match_score, 60)
        else:
            # LLM unavailable — blend function matching + keywords + complexity
            base_score = (
                fn_match_score * 0.4 +
                keyword_score * 0.4 +
                complexity_bonus * 1.33  # Scale 15 max → 20 max
            )

        # ── Step 6: Judge0 test execution (if test cases exist) ──
        if test_cases:
            judge0 = self._get_judge0()
            if judge0:
                test_score = judge0.compute_test_score(code, language, test_cases)
                feedback.append(
                    f"✓ Test execution: {test_score}% of test cases passed."
                )
                # Store for total score floor calculation
                self._last_test_pass_rate = test_score
                # Blend: 40% analysis + 60% ground-truth tests
                blended = 0.4 * base_score + 0.6 * test_score
                return min(round(blended), 100)
            else:
                feedback.append(
                    "⚠️ Judge0 unavailable. Falling back to analysis-only approach scoring."
                )

        return min(round(base_score), 100)

    def _function_name_relevance(
        self, function_names: List[str], problem: str, feedback: List[str]
    ) -> float:
        """
        Check if function/method names in the code match the problem description.

        This is a much stronger signal than keyword matching — if the student
        wrote a function called 'threeSum' and the problem mentions 'three sum',
        it's almost certainly relevant.

        Returns score 0-100.
        """
        if not function_names:
            return 40  # No functions to match, neutral score

        problem_lower = problem.lower()
        # Normalize problem: split camelCase and snake_case
        problem_tokens = set(re.findall(r'[a-z]+', problem_lower))

        best_match_score = 0

        for fn_name in function_names:
            if fn_name in ('__init__', 'main', 'setUp', 'tearDown'):
                continue  # Skip boilerplate

            # Split function name into tokens (camelCase + snake_case)
            fn_lower = fn_name.lower()
            fn_tokens = set(re.findall(r'[a-z]+', fn_lower))

            # Direct name match in problem text
            if fn_lower in problem_lower:
                best_match_score = max(best_match_score, 100)
                feedback.append(f"✓ Function '{fn_name}' directly matches the problem.")
                break

            # Token overlap (e.g., 'three_sum' matches 'threeSum')
            if fn_tokens and problem_tokens:
                overlap = fn_tokens & problem_tokens
                if overlap:
                    ratio = len(overlap) / len(fn_tokens)
                    match_score = min(ratio * 100, 95)
                    if match_score > best_match_score:
                        best_match_score = match_score
                        if ratio >= 0.5:
                            feedback.append(
                                f"✓ Function '{fn_name}' tokens match problem ({len(overlap)} matches)."
                            )

        return best_match_score

    def _keyword_relevance_score(
        self, code: str, problem: str, feedback: List[str], llm_verdict: Optional[str]
    ) -> float:
        """
        Compute keyword-based relevance score (language-agnostic).

        v2.1: Improved keyword extraction — uses longer words and filters
        more aggressively to avoid false matches on common terms.
        """
        # Extract meaningful keywords (5+ chars to avoid noise)
        problem_keywords = [
            w for w in set(re.findall(r'\b\w{5,}\b', problem.lower()))
            if w not in self.STOP_WORDS
        ]

        code_lower = code.lower()
        covered_keywords = [w for w in problem_keywords if w in code_lower]
        missing_keywords = [w for w in problem_keywords if w not in code_lower]

        self._last_missing_concepts = missing_keywords

        total_keywords = len(problem_keywords)
        match_ratio = len(covered_keywords) / total_keywords if total_keywords > 0 else 0

        # Score based on match ratio
        if total_keywords == 0:
            score = 55  # No keywords to match — neutral
            feedback.append("ℹ No problem keywords suitable for matching.")
        elif match_ratio >= 0.4 or len(covered_keywords) >= 4:
            score = 85
            feedback.append(
                f"✓ Good keyword alignment ({len(covered_keywords)}/{total_keywords} keywords found)."
            )
        elif match_ratio >= 0.2 or len(covered_keywords) >= 2:
            score = 70
            feedback.append(
                f"Code shows moderate relevance ({len(covered_keywords)}/{total_keywords} keywords)."
            )
        elif match_ratio > 0:
            score = 50
            feedback.append(
                f"Low keyword match ({int(match_ratio * 100)}%). "
                f"Code may not fully address the problem."
            )
        else:
            score = 30
            feedback.append(
                f"Very low keyword match. Code may not address the problem. "
                f"(Found 0/{total_keywords} keywords)."
            )

        return min(score, 100)

    # ======================================================================
    # READABILITY — (kept mostly unchanged, works for both languages)
    # ======================================================================

    def _evaluate_readability(
        self, code: str, feedback: List[str], language: str = "python"
    ) -> float:
        """Evaluate code readability."""
        score = 0
        lines = code.split("\n")

        # Line length check
        long_lines = sum(1 for line in lines if len(line.strip()) > 100)
        if long_lines == 0:
            score += 60
            feedback.append("Line length is appropriate for readability.")
        else:
            feedback.append(
                f"→ {long_lines} lines exceed 100 characters. "
                "Break them into shorter lines."
            )

        # Comment check (language-specific)
        if language == "python":
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        else:
            single_line_comments = sum(1 for line in lines if "//" in line)
            multi_line_comments = len(re.findall(r'/\*.*?\*/', code, re.DOTALL))
            comment_lines = single_line_comments + multi_line_comments

        if comment_lines > 0:
            score += 40
            feedback.append(f"Code includes comments ({comment_lines} found).")
        else:
            feedback.append("→ Add comments to explain your logic.")

        return min(score, 100)

    # ======================================================================
    # STRUCTURE — now uses the unified features dict
    # ======================================================================

    def _evaluate_structure(
        self,
        code: str,
        feedback: List[str],
        language: str = "python",
        features: Dict = None,
    ) -> float:
        """Evaluate code structure and organization using parsed features."""
        score = 0

        if features is None:
            features = extract_features(code, language)

        if features.get("has_syntax_error"):
            return 0

        total_definitions = features.get("functions", 0) + features.get("classes", 0)

        if total_definitions > 0:
            score += 50
            feedback.append(
                f"Good modularization ({total_definitions} functions/classes)."
            )
        else:
            feedback.append(
                "→ Consider breaking code into functions for reusability."
            )

        # Language-specific bonus checks
        if language == "python":
            # Check for variable assignments as proxy for structured logic
            lines = code.split("\n")
            assignments = sum(1 for line in lines if "=" in line and "==" not in line)
            if assignments > 0:
                score += 30
                feedback.append("Code uses variable assignments (structured logic).")
        elif language == "cpp":
            if 'namespace' in code or 'std::' in code or ('#ifndef' in code and '#define' in code):
                score += 30
                feedback.append("✓ Code uses namespaces/guards (good C++ practice).")

        # Error handling bonus (tree-sitter detects try/catch across languages)
        if features.get("error_handling", 0) > 0:
            score += 10
            feedback.append(
                f"✓ Code includes error handling "
                f"({features['error_handling']} try/catch blocks)."
            )

        # Nesting depth bonus — indicates thoughtful algorithm design
        max_depth = features.get("max_nesting_depth", 0)
        if max_depth >= 3:
            score += 10
            feedback.append(
                f"✓ Code has meaningful nesting depth ({max_depth} levels)."
            )

        return min(score, 100)

    # ======================================================================
    # EFFORT — v2.1 uses complexity_score for differentiation
    # ======================================================================

    def _evaluate_effort(
        self,
        code: str,
        feedback: List[str],
        language: str = "python",
        features: Dict = None,
    ) -> float:
        """Evaluate visible effort and complexity using parsed features."""
        score = 0

        if features is None:
            features = extract_features(code, language)

        lines = code.split("\n")
        # Filter comments
        if language == "python":
            non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        else:
            non_empty = [l for l in lines if l.strip() and not l.strip().startswith("//")]

        code_lines = len(non_empty)

        if code_lines > 10:
            score += 40
            feedback.append(f"Substantial code submission ({code_lines} lines).")
        elif code_lines > 5:
            score += 30
            feedback.append(f"Moderate code submission ({code_lines} lines).")
        elif code_lines > 0:
            score += 15
            feedback.append(
                "→ Your solution is brief. Consider adding more logic or cases."
            )

        # Control flow from features (unified — no more if/else per language)
        control_flow = features.get("loops", 0) + features.get("conditions", 0)
        if control_flow > 0:
            score += 30
            feedback.append(
                f"✓ Code includes control flow ({control_flow} conditions/loops)."
            )

        # Unique identifiers bonus — more variables = more specific logic
        unique_ids = features.get("unique_identifiers", 0)
        if unique_ids >= 10:
            score += 20
            feedback.append(
                f"✓ Code uses diverse identifiers ({unique_ids} unique names)."
            )
        elif unique_ids >= 5:
            score += 10
            feedback.append(
                f"Code uses moderate variable diversity ({unique_ids} unique names)."
            )

        # Complexity bonus — the composite score differentiates algorithms
        complexity = features.get("complexity_score", 0)
        if complexity >= 50:
            score += 10
            feedback.append(
                f"✓ Code demonstrates good algorithmic complexity (score: {complexity})."
            )

        return min(score, 100)
