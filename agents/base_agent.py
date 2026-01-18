from abc import ABC, abstractmethod
from typing import Any, Dict, List


class EvaluationAgent(ABC):
    """Abstract base class for evaluation agents."""

    @abstractmethod
    def evaluate(self, input_data: Any) -> Dict[str, Any]:
        """
        Evaluate the input data and return results.

        Args:
            input_data: The input data to evaluate.

        Returns:
            A dictionary containing:
                - score: The evaluation score
                - max_score: The maximum possible score
                - feedback: A list of feedback strings
        """
        pass
