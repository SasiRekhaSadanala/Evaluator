import re
from typing import Any, Dict, List

from .base_agent import EvaluationAgent
from utils.llm_service import LLMService


class ContentEvaluationAgent(EvaluationAgent):
    """Evaluates student content (PPT text, summaries) through structural analysis."""

    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()

    def evaluate(self, input_data: Any) -> Dict[str, Any]:
        """
        Evaluate student content through structural and keyword analysis.

        Args:
            input_data: Dictionary containing:
                - student_content (str): The student's text content
                - rubric (dict): Evaluation criteria with key concepts, OR
                - ideal_reference (str): Reference content for comparison

        Returns:
            Dictionary with:
                - score: Total evaluation score
                - max_score: Maximum possible score
                - feedback: List of learning-oriented feedback strings
        """
        student_content = input_data.get("student_content", "")
        rubric = input_data.get("rubric", {})
        ideal_reference = input_data.get("ideal_reference", "")

        feedback = []
        scores = {}

        # Extract key concepts from rubric or reference
        key_concepts = self._extract_key_concepts(rubric, ideal_reference)

        # Analyze concept coverage
        coverage_score = self._evaluate_concept_coverage(
            student_content, key_concepts, feedback
        )
        scores["coverage"] = coverage_score

        # Analyze alignment with requirements
        alignment_score = self._evaluate_alignment(
            student_content, rubric, feedback
        )
        scores["alignment"] = alignment_score

        # Analyze logical flow
        flow_score = self._evaluate_logical_flow(student_content, feedback)
        scores["flow"] = flow_score

        # Analyze completeness
        completeness_score = self._evaluate_completeness(student_content, feedback)
        scores["completeness"] = completeness_score

        # Calculate total score with weights
        weights = {
            "coverage": 0.35,
            "alignment": 0.25,
            "flow": 0.2,
            "completeness": 0.2,
        }

        total_score = sum(scores.get(k, 0) * v for k, v in weights.items())
        max_score = sum(weights.values()) * 100

        # Integrate LLM Feedback (Step 2, 4, 5)
        if self.llm_service.enabled:
            # Collect missing concepts for semantic explanation (Step 4)
            missing_concepts = getattr(self, "_last_missing_concepts", [])
            
            # Collect deterministic findings for context
            findings = [f for f in feedback if f.startswith("✓") or f.startswith("→")]
            
            llm_feedback = self.llm_service.generate_semantic_feedback(
                context_type="content",
                submission_content=student_content,
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

    def _extract_key_concepts(self, rubric: dict, ideal_reference: str) -> List[str]:
        """Extract key concepts from rubric or reference."""
        concepts = []

        if rubric:
            # Extract from rubric concepts or criteria
            if "concepts" in rubric:
                concepts.extend(rubric["concepts"])
            if "criteria" in rubric:
                criteria = rubric["criteria"]
                if isinstance(criteria, list):
                    concepts.extend(criteria)
                elif isinstance(criteria, dict):
                    concepts.extend(criteria.keys())

        if ideal_reference:
            # Extract key terms (longer words) from reference
            words = re.findall(r"\b\w{4,}\b", ideal_reference.lower())
            concepts.extend(list(set(words))[:10])  # Top unique words

        return list(set(concepts))  # Remove duplicates

    def _evaluate_concept_coverage(
        self, content: str, key_concepts: List[str], feedback: List[str]
    ) -> float:
        """Evaluate coverage of key concepts."""
        score = 40

        if not key_concepts:
            feedback.append("ℹ No key concepts specified for comparison.")
            return 60

        content_lower = content.lower()
        covered_concepts = [
            c for c in key_concepts
            if isinstance(c, str) and c.lower() in content_lower
        ]
        missing_concepts = [
            c for c in key_concepts
            if isinstance(c, str) and c.lower() not in content_lower
        ]
        
        # Store for LLM use
        self._last_missing_concepts = missing_concepts
        
        coverage_percent = (len(covered_concepts) / len(key_concepts)) * 100 if key_concepts else 0

        if coverage_percent >= 80:
            score += 50
            feedback.append(
                f"✓ Excellent concept coverage ({len(covered_concepts)}/{len(key_concepts)} concepts)."
            )
        elif coverage_percent >= 60:
            score += 30
            msg = f"→ Good coverage ({len(covered_concepts)}/{len(key_concepts)} concepts). "
            # Step 4: No raw keywords if LLM is enabled
            if not self.llm_service.enabled:
                msg += f"Missing: {', '.join(missing_concepts[:3])}"
            feedback.append(msg)
        elif coverage_percent >= 40:
            score += 15
            feedback.append(
                f"→ Partial coverage ({len(covered_concepts)}/{len(key_concepts)} concepts). "
                "Add more required concepts to your content."
            )
        else:
            feedback.append(
                f"❌ Low concept coverage ({len(covered_concepts)}/{len(key_concepts)} concepts). "
                "Review and include all key concepts."
            )

        return min(score, 100)

    def _evaluate_alignment(
        self, content: str, rubric: dict, feedback: List[str]
    ) -> float:
        """Evaluate alignment with rubric requirements."""
        score = 50

        if not rubric:
            return score

        # Check for learning objectives match
        if "learning_objectives" in rubric:
            objectives = rubric["learning_objectives"]
            if isinstance(objectives, list):
                matched = sum(
                    1 for obj in objectives
                    if isinstance(obj, str) and obj.lower() in content.lower()
                )
                if matched > 0:
                    score += 30
                    feedback.append(
                        f"✓ Addresses {matched} learning objectives."
                    )
                else:
                    feedback.append("→ Content should align with stated learning objectives.")

        # Check for required sections
        if "required_sections" in rubric:
            sections = rubric["required_sections"]
            if isinstance(sections, list):
                matched_sections = sum(
                    1 for sec in sections
                    if isinstance(sec, str) and sec.lower() in content.lower()
                )
                if matched_sections >= len(sections) * 0.7:
                    score += 20
                    feedback.append(
                        f"✓ Includes most required sections ({matched_sections}/{len(sections)})."
                    )
                else:
                    feedback.append(
                        f"→ Missing some required sections. "
                        f"Found {matched_sections}/{len(sections)}."
                    )

        return min(score, 100)

    def _evaluate_logical_flow(self, content: str, feedback: List[str]) -> float:
        """Evaluate logical flow and organization."""
        score = 50

        lines = content.split("\n")
        paragraphs = [p.strip() for p in lines if p.strip()]
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Check paragraph structure
        if len(paragraphs) > 3:
            score += 25
            feedback.append(f"✓ Well-organized ({len(paragraphs)} distinct sections).")
        elif len(paragraphs) > 1:
            score += 15
            feedback.append("→ Consider organizing content into more distinct sections.")
        else:
            feedback.append("→ Break content into multiple paragraphs for clarity.")

        # Check sentence complexity and variety
        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences)
            if sentences else 0
        )

        if 10 < avg_sentence_length < 25:
            score += 15
            feedback.append("✓ Sentence structure is clear and varied.")
        elif avg_sentence_length > 30:
            feedback.append(
                "→ Some sentences are too long. Break them for clarity."
            )
        elif avg_sentence_length < 5:
            feedback.append(
                "→ Sentences are too short. Expand with more detail."
            )

        # Check for transitions (simple keyword check)
        transition_words = [
            "therefore", "however", "additionally", "moreover", "furthermore",
            "in conclusion", "as a result", "for example", "similarly",
            "in contrast", "meanwhile", "next", "finally"
        ]
        transitions = sum(
            1 for word in transition_words if word in content.lower()
        )

        if transitions >= 3:
            score += 10
            feedback.append("✓ Good use of transitions for logical flow.")
        elif transitions > 0:
            feedback.append("→ Add more transition words to improve flow between ideas.")

        return min(score, 100)

    def _evaluate_completeness(self, content: str, feedback: List[str]) -> float:
        """Evaluate content completeness and detail."""
        score = 50

        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]
        word_count = len(content.split())

        # Check content length
        if word_count > 300:
            score += 30
            feedback.append(f"✓ Substantial content ({word_count} words).")
        elif word_count > 150:
            score += 15
            feedback.append(f"→ Content is moderate ({word_count} words). Add more detail.")
        else:
            feedback.append(
                f"→ Content is brief ({word_count} words). Expand with examples and explanations."
            )

        # Check for examples or details
        example_indicators = [
            "example", "for instance", "such as", "specifically",
            "in particular", "illustration", "case study"
        ]
        has_examples = any(
            indicator in content.lower() for indicator in example_indicators
        )

        if has_examples:
            score += 10
            feedback.append("✓ Includes examples or specific details.")
        else:
            feedback.append("→ Add concrete examples to support your concepts.")

        # Check for evidence or reasoning
        reasoning_indicators = [
            "because", "reason", "evidence", "research", "study",
            "proven", "demonstrated", "support", "justify"
        ]
        has_reasoning = any(
            indicator in content.lower() for indicator in reasoning_indicators
        )

        if has_reasoning:
            score += 10
            feedback.append("✓ Includes reasoning or evidence.")
        else:
            feedback.append("→ Add reasoning or evidence to strengthen claims.")

        return min(score, 100)
