"""Case evaluation module for running LLM summarization."""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict

from langchain_core.language_models import BaseChatModel
from tqdm import tqdm

from .config import EvaluationConfig
from .init_model import count_tokens
from .rate_limiter import RateLimiter
from .read_all_cases import CaseDescAndData
from .strip_delimeters import strip_delimeters


class CaseEvaluator:
    """Handles evaluation of medical cases using LLM summarization.

    Coordinates the entire evaluation process including:
    - Loading and filtering cases
    - Applying rate limiting
    - Generating summaries
    - Saving results
    - Error handling and logging
    """

    def __init__(
        self,
        config: EvaluationConfig,
        llm: BaseChatModel,
        model_id: str,
        summarize_fn: Callable[[BaseChatModel, str, str], Any],
    ):
        """Initialize the case evaluator.

        Args:
            config: Evaluation configuration
            llm: Language model instance
            model_id: String identifier for the model
            summarize_fn: Function that takes (llm, language, text) and returns summary or result dict
        """
        self.config = config
        self.llm = llm
        self.model_id = model_id
        self.summarize_fn = summarize_fn
        self.rate_limiter = RateLimiter(config.rate_limit_seconds)
        self.logger = logging.getLogger(__name__)

        # Track statistics
        self.total_cases = 0
        self.successful_cases = 0
        self.failed_cases = 0

        # Track metadata across all cases
        self.metadata_log = []
        self.successful_cases = 0
        self.failed_cases = 0

    def save_output(self, dest: Path, file_name: str, content: str) -> None:
        """Save the output string to a file.

        Args:
            dest: Destination directory
            file_name: Name of the output file
            content: Content to write
        """
        content = strip_delimeters(content)

        output_path = dest / file_name
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def process_case(self, case: CaseDescAndData) -> bool:
        """Process a single case and generate summary.

        Args:
            case: Case data to process

        Returns:
            True if successful, False if failed
        """
        self.logger.info("Processing case %s...", case.case_id)

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            # Track time and tokens
            import time

            start_time = time.time()

            # Generate summary (can return string or dict with metadata)
            result = self.summarize_fn(
                self.llm,
                case.object.language,
                case.text,
            )

            # Handle different return types
            if isinstance(result, dict):
                # Agentic approaches return dict with summary and metadata
                summary = result.get("summary", "")
                metadata = {
                    "case_id": case.case_id,
                    "approach": self.config.approach,
                    "latency_seconds": time.time() - start_time,
                    "input_tokens": count_tokens(case.text, self.config.model_name),
                    "output_tokens": count_tokens(summary, self.config.model_name),
                }
                # Add any additional metadata from result
                metadata.update({k: v for k, v in result.items() if k != "summary"})
            else:
                # Basic approach returns string
                summary = result
                metadata = {
                    "case_id": case.case_id,
                    "approach": self.config.approach,
                    "latency_seconds": time.time() - start_time,
                    "input_tokens": count_tokens(case.text, self.config.model_name),
                    "output_tokens": count_tokens(summary, self.config.model_name),
                    "num_api_calls": 1,
                }

            # Calculate total tokens
            metadata["total_tokens"] = (
                metadata["input_tokens"] + metadata["output_tokens"]
            )

            # Save metadata
            self.metadata_log.append(metadata)

            # Save output
            prefix = f"Summary_4_{case.case_id}@{case.language}@${self.model_id}"
            file_name = f"{prefix}@{self.config.approach}.txt"
            self.save_output(self.config.output_dir, file_name, summary)

            # Log summary statistics
            self.logger.info(
                "Saved output for case %s (tokens: %d in/%d out, time: %.1fs)",
                case.case_id,
                metadata["input_tokens"],
                metadata["output_tokens"],
                metadata["latency_seconds"],
            )

            # Log additional info for agentic approaches
            if "iterations" in metadata:
                self.logger.info(
                    "  └─ Iterations: %d, API calls: %d",
                    metadata["iterations"],
                    metadata.get("num_api_calls", 0),
                )

            return True

        except Exception as e:
            self.logger.error(
                "Error processing case %s: %s",
                case.case_id,
                str(e),
                exc_info=True,
            )
            return False

    def run(self, cases: dict[str, CaseDescAndData]) -> None:
        """Run evaluation on all cases.

        Args:
            cases: Dictionary of case_id to case data
        """
        self.total_cases = len(cases)
        self.logger.info("Starting evaluation of %d cases", self.total_cases)

        # Create output directory if needed
        if not self.config.output_dir.exists():
            self.config.output_dir.mkdir(parents=True)
            self.logger.info("Created output directory: %s", self.config.output_dir)

        # Process all cases with progress bar
        for case in tqdm(cases.values(), desc="Processing cases"):
            success = self.process_case(case)
            if success:
                self.successful_cases += 1
            else:
                self.failed_cases += 1

        # Log final statistics
        self.logger.info("Processing complete.")
        self.logger.info(
            "Results: %d successful, %d failed out of %d total",
            self.successful_cases,
            self.failed_cases,
            self.total_cases,
        )

        if self.failed_cases > 0:
            self.logger.warning(
                "Warning: %d cases failed. Check logs for details.", self.failed_cases
            )

        # Save metadata summary
        if self.metadata_log:
            self._save_metadata_summary()

    def _save_metadata_summary(self) -> None:
        """Save aggregated metadata to JSON file."""
        metadata_file = self.config.output_dir / "metadata_summary.json"

        # Calculate aggregate statistics
        total_tokens = sum(m["total_tokens"] for m in self.metadata_log)
        total_latency = sum(m["latency_seconds"] for m in self.metadata_log)
        avg_latency = total_latency / len(self.metadata_log) if self.metadata_log else 0

        summary = {
            "approach": self.config.approach,
            "model": self.model_id,
            "total_cases": self.total_cases,
            "successful_cases": self.successful_cases,
            "failed_cases": self.failed_cases,
            "total_tokens": total_tokens,
            "total_latency_seconds": total_latency,
            "average_latency_seconds": avg_latency,
            "cases": self.metadata_log,
        }

        # Add approach-specific statistics
        if self.config.approach == "reflection":
            total_iterations = sum(m.get("iterations", 0) for m in self.metadata_log)
            total_api_calls = sum(m.get("num_api_calls", 0) for m in self.metadata_log)
            summary["total_iterations"] = total_iterations
            summary["total_api_calls"] = total_api_calls
            summary["average_iterations"] = (
                total_iterations / len(self.metadata_log) if self.metadata_log else 0
            )
            summary["average_api_calls"] = (
                total_api_calls / len(self.metadata_log) if self.metadata_log else 0
            )

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        self.logger.info("Saved metadata summary to: %s", metadata_file)
        self.logger.info(
            "Total tokens used: %d (%.2f per case)",
            total_tokens,
            total_tokens / len(self.metadata_log) if self.metadata_log else 0,
        )
        self.logger.info("Average latency: %.1f seconds", avg_latency)
