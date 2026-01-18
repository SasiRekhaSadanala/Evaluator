import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class Rubric:
    """Manages evaluation rubric structure, weights, and validation."""

    DEFAULT_RUBRIC = {
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

    def __init__(self, rubric_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize rubric from dict or use default.

        Args:
            rubric_dict: Rubric dictionary, or None to use default
        """
        if rubric_dict is None:
            self.rubric = self.DEFAULT_RUBRIC.copy()
        else:
            self.rubric = rubric_dict

        # Validate on initialization
        self.validate()

    @staticmethod
    def from_json(json_path: str) -> "Rubric":
        """
        Load rubric from JSON file.

        Args:
            json_path: Path to JSON file containing rubric

        Returns:
            Rubric instance
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Rubric file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            rubric_dict = json.load(f)

        return Rubric(rubric_dict)

    @staticmethod
    def from_json_string(json_string: str) -> "Rubric":
        """
        Load rubric from JSON string.

        Args:
            json_string: JSON string containing rubric

        Returns:
            Rubric instance
        """
        rubric_dict = json.loads(json_string)
        return Rubric(rubric_dict)

    def validate(self) -> None:
        """
        Validate rubric structure.

        Raises:
            ValueError: If rubric structure is invalid
        """
        if not isinstance(self.rubric, dict):
            raise ValueError("Rubric must be a dictionary")

        if "dimensions" not in self.rubric:
            raise ValueError("Rubric must contain 'dimensions' key")

        dimensions = self.rubric["dimensions"]
        if not isinstance(dimensions, dict):
            raise ValueError("'dimensions' must be a dictionary")

        # Validate required dimensions
        required_dimensions = {"code", "content"}
        found_dimensions = set(dimensions.keys())

        if not required_dimensions.issubset(found_dimensions):
            missing = required_dimensions - found_dimensions
            raise ValueError(
                f"Rubric missing required dimensions: {missing}"
            )

        # Validate each dimension
        total_weight = 0
        for dim_name, dim_config in dimensions.items():
            if not isinstance(dim_config, dict):
                raise ValueError(f"Dimension '{dim_name}' must be a dictionary")

            if "weight" not in dim_config:
                raise ValueError(f"Dimension '{dim_name}' missing 'weight'")

            weight = dim_config["weight"]
            if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
                raise ValueError(
                    f"Dimension '{dim_name}' weight must be between 0 and 1"
                )

            total_weight += weight

            if "max_score" not in dim_config:
                raise ValueError(f"Dimension '{dim_name}' missing 'max_score'")

            max_score = dim_config["max_score"]
            if not isinstance(max_score, (int, float)) or max_score <= 0:
                raise ValueError(
                    f"Dimension '{dim_name}' max_score must be positive"
                )

        # Weights should sum to 1.0 (allow small floating point error)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(
                f"Dimension weights must sum to 1.0, got {total_weight}"
            )

    def get_weight(self, dimension: str) -> float:
        """
        Get weight for a dimension.

        Args:
            dimension: Dimension name ('code' or 'content')

        Returns:
            Weight as a float
        """
        if dimension not in self.rubric["dimensions"]:
            raise ValueError(f"Unknown dimension: {dimension}")

        return self.rubric["dimensions"][dimension]["weight"]

    def get_max_score(self, dimension: str) -> float:
        """
        Get max score for a dimension.

        Args:
            dimension: Dimension name ('code' or 'content')

        Returns:
            Max score as a float
        """
        if dimension not in self.rubric["dimensions"]:
            raise ValueError(f"Unknown dimension: {dimension}")

        return self.rubric["dimensions"][dimension]["max_score"]

    def get_weights(self) -> Dict[str, float]:
        """
        Get all dimension weights.

        Returns:
            Dictionary of dimension names to weights
        """
        return {
            dim: config["weight"]
            for dim, config in self.rubric["dimensions"].items()
        }

    def get_max_scores(self) -> Dict[str, float]:
        """
        Get all dimension max scores.

        Returns:
            Dictionary of dimension names to max scores
        """
        return {
            dim: config["max_score"]
            for dim, config in self.rubric["dimensions"].items()
        }

    def get_criteria(self, dimension: str) -> Dict[str, Dict[str, Any]]:
        """
        Get criteria for a dimension.

        Args:
            dimension: Dimension name ('code' or 'content')

        Returns:
            Dictionary of criteria configurations
        """
        if dimension not in self.rubric["dimensions"]:
            raise ValueError(f"Unknown dimension: {dimension}")

        return self.rubric["dimensions"][dimension].get("criteria", {})

    def get_dimension_config(self, dimension: str) -> Dict[str, Any]:
        """
        Get full configuration for a dimension.

        Args:
            dimension: Dimension name ('code' or 'content')

        Returns:
            Dictionary with dimension configuration
        """
        if dimension not in self.rubric["dimensions"]:
            raise ValueError(f"Unknown dimension: {dimension}")

        return self.rubric["dimensions"][dimension]

    def get_total_max_score(self) -> float:
        """
        Get total maximum score across all dimensions.

        Returns:
            Sum of all dimension max scores weighted by their weights
        """
        total = sum(
            self.get_max_score(dim) * self.get_weight(dim)
            for dim in self.rubric["dimensions"]
        )
        return round(total, 2)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export rubric as dictionary.

        Returns:
            Rubric dictionary
        """
        return self.rubric.copy()

    def to_json(self) -> str:
        """
        Export rubric as JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.rubric, indent=2)
