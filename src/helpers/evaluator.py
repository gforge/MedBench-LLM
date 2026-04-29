"""Case evaluation module for running LLM summarization."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from langchain_core.language_models import BaseChatModel
from openai import AuthenticationError, NotFoundError, PermissionDeniedError
from pydantic import BaseModel
from tqdm import tqdm

from .config import EvaluationConfig
from .init_model import available_models, count_tokens
from .rate_limiter import RateLimiter
from .read_all_cases import CaseDescAndData
from .strip_delimeters import strip_delimeters
from .summarize_result import SummarizeFn, SummarizeResult


class CaseMetadata(BaseModel):
    """Typed metadata record for each processed case."""

    case_id: str
    language: str
    approach: str
    started_at_utc: str
    completed_at_utc: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    num_api_calls: int = 1
    iterations: int | None = None
    total_tokens: int = 0

    model_config = {"extra": "ignore", "validate_assignment": True}


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
        summarize_fn: SummarizeFn,
    ):
        """Initialize the case evaluator.

        Args:
            config: Evaluation configuration
            llm: Language model instance
            model_id: String identifier for the model
            summarize_fn: Function that takes (llm, language, case) and returns SummarizeResult
        """
        self.config: EvaluationConfig = config
        self.llm: BaseChatModel = llm
        self.model_id: str = model_id
        self.summarize_fn: SummarizeFn = summarize_fn
        self.rate_limiter: RateLimiter = RateLimiter(config.rate_limit_seconds)
        self.logger: logging.Logger = logging.getLogger(__name__)

        # Track statistics
        self.total_cases = 0
        self.successful_cases = 0
        self.failed_cases = 0

        # Track metadata across all cases
        self.metadata_log: List[CaseMetadata] = []
        self.run_started_at_utc: str | None = None
        self.run_completed_at_utc: str | None = None
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

            started_at = datetime.now(timezone.utc)
            start_time = time.time()

            # Generate summary using unified interface
            result: SummarizeResult = self.summarize_fn(
                self.llm,
                case.object.language,
                case.object,
            )

            completed_at = datetime.now(timezone.utc)

            # Build metadata from result
            metadata = CaseMetadata(
                case_id=case.case_id,
                language=case.language,
                approach=self.config.approach,
                started_at_utc=started_at.isoformat(),
                completed_at_utc=completed_at.isoformat(),
                latency_seconds=time.time() - start_time,
                input_tokens=count_tokens(case.text, self.config.model_name),
                output_tokens=count_tokens(result.summary, self.config.model_name),
                num_api_calls=result.num_api_calls,
                iterations=result.iterations,
            )
            metadata.total_tokens = metadata.input_tokens + metadata.output_tokens

            # Save metadata (keep typed objects in-memory)
            self.metadata_log.append(metadata)

            # Save output
            prefix = f"Summary_4_{case.case_id}@{case.language}@${self.model_id}"
            file_name = f"{prefix}@{self.config.approach}.txt"
            self.save_output(self.config.output_dir, file_name, result.summary)

            # Log summary statistics
            self.logger.info(
                "Saved output for case %s (tokens: %d in/%d out, time: %.1fs)",
                case.case_id,
                metadata.input_tokens,
                metadata.output_tokens,
                metadata.latency_seconds,
            )

            # Log additional info for agentic approaches
            if metadata.iterations is not None:
                self.logger.info(
                    "  └─ Iterations: %d, API calls: %d",
                    metadata.iterations,
                    metadata.num_api_calls,
                )

            return True

        except (NotFoundError, AuthenticationError, PermissionDeniedError) as e:
            # Fatal API errors - don't continue processing
            self.logger.error(
                "Fatal API error processing case %s: %s",
                case.case_id,
                str(e),
            )
            raise  # Re-raise to stop the entire evaluation

        except FileNotFoundError as e:
            # All files must exist, so this is a critical error
            self.logger.error(
                "File not found for case %s: %s",
                case.case_id,
                str(e),
            )
            raise

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
        self.run_started_at_utc = datetime.now(timezone.utc).isoformat()
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
            self.logger.warning("Warning: %d cases failed. Check logs for details.", self.failed_cases)

        # Save metadata summary
        self.run_completed_at_utc = datetime.now(timezone.utc).isoformat()
        self._save_metadata_summary()

    def _save_metadata_summary(self) -> None:
        """Save aggregated metadata to JSON file."""
        metadata_file = self.config.output_dir / "metadata_summary.json"

        # Calculate aggregate statistics
        total_tokens = sum(m.total_tokens for m in self.metadata_log)
        total_latency = sum(m.latency_seconds for m in self.metadata_log)
        avg_latency = total_latency / len(self.metadata_log) if self.metadata_log else 0
        model_definition = available_models.get(self.config.model_name)

        model_details = {
            "selection_name": self.config.model_name,
            "deployment": model_definition.deployment if model_definition else None,
            "name": model_definition.name if model_definition else None,
            "version": model_definition.version if model_definition else None,
            "api_version": model_definition.api_version if model_definition else None,
            "resolved_model_id": self.model_id,
        }

        summary = {
            "run_started_at_utc": self.run_started_at_utc,
            "run_completed_at_utc": self.run_completed_at_utc,
            "approach": self.config.approach,
            "model": self.model_id,
            "model_details": model_details,
            "specialty": self.config.specialty,
            "languages": self.config.languages,
            "require_complete_language_set": self.config.require_complete_language_set,
            "temperature": self.config.temperature,
            "rate_limit_seconds": self.config.rate_limit_seconds,
            "total_cases": self.total_cases,
            "successful_cases": self.successful_cases,
            "failed_cases": self.failed_cases,
            "total_tokens": total_tokens,
            "total_latency_seconds": total_latency,
            "average_latency_seconds": avg_latency,
            "cases": [m.model_dump() for m in self.metadata_log],
        }

        # Add approach-specific statistics
        if self.config.approach == "reflection":
            total_iterations = sum((m.iterations or 0) for m in self.metadata_log)
            total_api_calls = sum((m.num_api_calls or 0) for m in self.metadata_log)
            summary["total_iterations"] = total_iterations
            summary["total_api_calls"] = total_api_calls
            summary["average_iterations"] = total_iterations / len(self.metadata_log) if self.metadata_log else 0
            summary["average_api_calls"] = total_api_calls / len(self.metadata_log) if self.metadata_log else 0

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        self.logger.info("Saved metadata summary to: %s", metadata_file)
        self.logger.info(
            "Total tokens used: %d (%.2f per case)",
            total_tokens,
            total_tokens / len(self.metadata_log) if self.metadata_log else 0,
        )
        self.logger.info("Average latency: %.1f seconds", avg_latency)
