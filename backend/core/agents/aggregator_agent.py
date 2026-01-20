from typing import Any, Dict, List

from .base_agent import EvaluationAgent


class AggregatorAgent(EvaluationAgent):
    """Aggregates outputs from multiple evaluation agents."""

    def evaluate(self, input_data: Any) -> Dict[str, Any]:
        """
        Aggregate multiple agent outputs into a final evaluation.

        Args:
            input_data: Dictionary containing:
                - agent_outputs (list): List of dicts from individual agents,
                  each with 'score', 'max_score', 'feedback'
                - rubric (dict): Weighting for each agent/dimension

        Returns:
            Dictionary with:
                - final_score: Aggregated and normalized score
                - max_score: Maximum possible score
                - combined_feedback: List of all unique feedback items organized
        """
        agent_outputs = input_data.get("agent_outputs", [])
        rubric = input_data.get("rubric", {})

        if not agent_outputs:
            return {
                "final_score": 0,
                "max_score": 100,
                "combined_feedback": ["No agent outputs to evaluate."],
            }

        # Extract scores and feedback
        scores = []
        all_feedback = []
        agent_names = []

        for i, output in enumerate(agent_outputs):
            score = output.get("score", 0)
            max_score = output.get("max_score", 100)
            feedback = output.get("feedback", [])

            # Normalize score to 0-100 scale
            normalized_score = self._normalize_score(score, max_score)
            scores.append(normalized_score)

            # Collect feedback
            if isinstance(feedback, list):
                all_feedback.extend(feedback)
            elif isinstance(feedback, str):
                all_feedback.append(feedback)

            agent_names.append(f"Agent_{i+1}")

        # Apply weights from rubric
        weights = self._get_weights(rubric, len(scores))

        # Calculate weighted final score
        final_score = sum(s * w for s, w in zip(scores, weights))
        final_score = self._apply_learning_oriented_normalization(final_score)

        # Combine and deduplicate feedback
        combined_feedback = self._combine_feedback(all_feedback)

        max_score = 100

        return {
            "final_score": round(final_score, 2),
            "max_score": max_score,
            "combined_feedback": combined_feedback,
        }

    def _normalize_score(self, score: float, max_score: float) -> float:
        """Normalize score to 0-100 scale."""
        if max_score == 0:
            return 0
        return (score / max_score) * 100

    def _get_weights(self, rubric: dict, num_agents: int) -> List[float]:
        """Get weights from rubric or use uniform weights."""
        if rubric and "weights" in rubric:
            weights = rubric["weights"]
            if isinstance(weights, list):
                # Pad or truncate to match number of agents
                if len(weights) < num_agents:
                    remaining = 1.0 - sum(weights)
                    weights.extend([remaining / (num_agents - len(weights))] * (num_agents - len(weights)))
                elif len(weights) > num_agents:
                    weights = weights[:num_agents]
                # Normalize to sum to 1.0
                total = sum(weights)
                return [w / total for w in weights]

        # Default: equal weights
        return [1.0 / num_agents] * num_agents

    def _apply_learning_oriented_normalization(self, score: float) -> float:
        """
        Apply learning-oriented normalization (curves are forgiving).
        Scores are not harshly penalized; focus is on growth potential.
        """
        # Shift lower scores up slightly to be encouraging but fair
        if score < 40:
            # For very low scores, apply gentle curve: score * 1.1
            return min(score * 1.1, 40)
        elif score < 60:
            # For low-mid range, apply smaller adjustment
            return score * 1.05
        else:
            # For mid-to-high scores, keep as is
            return score

    def _combine_feedback(self, feedback_list: List[str]) -> List[str]:
        """Combine feedback, removing duplicates and organizing."""
        if not feedback_list:
            return ["No feedback available."]

        # Remove exact duplicates while preserving order
        seen = set()
        unique_feedback = []
        for item in feedback_list:
            if item not in seen:
                unique_feedback.append(item)
                seen.add(item)

        # Organize by type: strengths (✓), improvements (→), issues (❌)
        strengths = [f for f in unique_feedback if f.startswith("✓")]
        improvements = [f for f in unique_feedback if f.startswith("→")]
        issues = [f for f in unique_feedback if f.startswith("❌") or f.startswith("[x]")]
        llm_explanations = []
        is_llm_section = False
        
        # Extract LLM explanations while preserving their internal structure
        final_unique_feedback = []
        for f in unique_feedback:
            if "LLM Explanation:" in f:
                is_llm_section = True
                continue
            
            if is_llm_section:
                # If we hit a new section marker, we stop the LLM section
                if any(f.startswith(s) for s in ["✓", "→", "❌", "ℹ", "##", "[", "√"]):
                    is_llm_section = False
                else:
                    llm_explanations.append(f)
                    continue
            
            final_unique_feedback.append(f)

        neutral = [f for f in final_unique_feedback if not any(f.startswith(s) for s in ["✓", "→", "❌", "ℹ", "##", "["])]
        info = [f for f in final_unique_feedback if f.startswith("ℹ")]

        # Organize: AI Insights first (priority semantic feedback), then standard categories
        organized = []
        if llm_explanations:
            organized.append("## AI Evaluator")
            organized.extend(llm_explanations)
            organized.append("") # Spacer
            
        if strengths:
            organized.append("## Strengths")
            organized.extend(strengths)
        if improvements:
            organized.append("## Areas for Improvement")
            organized.extend(improvements)
        if issues:
            organized.append("## Issues to Address")
            organized.extend(issues)
        if info:
            organized.append("## Additional Notes")
            organized.extend(info)
        if neutral:
            organized.extend(neutral)

        return organized if organized else unique_feedback
