"""Configuration management for MedBench LLM evaluation."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from .init_model import AvailableModels


@dataclass
class EvaluationConfig:
    """Configuration for running LLM evaluation on medical cases.

    Attributes:
        specialty: Medical specialty to filter cases (e.g., "Medicine", "Surgery")
        language: Language filter for cases (e.g., "original", "Swedish", "English")
        model_name: Name of the LLM model to use
        temperature: Temperature parameter for LLM generation (0.0 = deterministic)
        rate_limit_seconds: Seconds to wait between API calls to avoid rate limiting
        data_dir: Base directory containing processed case data
        output_dir: Directory to save generated summaries
        approach: Summarization approach to use (e.g., "basic")
    """

    specialty: str
    language: str
    model_name: AvailableModels
    temperature: float
    rate_limit_seconds: int
    data_dir: Path
    output_dir: Path
    approach: str = "basic"

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "EvaluationConfig":
        """Create configuration from parsed command-line arguments.

        Args:
            args: Parsed arguments from argparse

        Returns:
            EvaluationConfig instance
        """
        project_folder = Path.cwd()
        data_dir = project_folder / "data" / "processed"
        output_dir = project_folder / "data" / "output" / args.specialty

        return cls(
            specialty=args.specialty,
            language=args.language,
            model_name=args.model,
            temperature=args.temperature,
            rate_limit_seconds=args.rate_limit,
            data_dir=data_dir,
            output_dir=output_dir,
            approach=args.approach,
        )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for evaluation configuration.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation on medical case summaries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--specialty",
        type=str,
        default="Medicine",
        help="Medical specialty to filter cases",
    )

    parser.add_argument(
        "--language",
        type=str,
        default="original",
        help="Language filter for cases (e.g., 'original', 'Swedish', 'English')",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5-mini",
        choices=["gpt-35", "gpt-4o-mini", "gpt-4-turbo", "gpt-5-mini"],
        help="LLM model to use for generation",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for LLM generation (0.0 = deterministic, higher = more random)",
    )

    parser.add_argument(
        "--rate-limit",
        type=int,
        default=60,
        help="Seconds to wait between API calls to avoid rate limiting",
    )

    parser.add_argument(
        "--approach",
        type=str,
        default="basic",
        choices=["basic", "reflection", "hierarchical"],
        help="Summarization approach to use",
    )

    return parser.parse_args()
