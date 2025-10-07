"""Case evaluation module for running LLM summarization."""

import logging
from pathlib import Path
from typing import Callable

from langchain_core.language_models import BaseChatModel
from tqdm import tqdm

from .config import EvaluationConfig
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
        summarize_fn: Callable[[BaseChatModel, str, str], str],
    ):
        """Initialize the case evaluator.

        Args:
            config: Evaluation configuration
            llm: Language model instance
            model_id: String identifier for the model
            summarize_fn: Function that takes (llm, language, text) and returns summary
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
            # Generate summary
            summary = self.summarize_fn(
                self.llm,
                case.object.language,
                case.text,
            )

            # Save output
            prefix = f"Summary_4_{case.case_id}@{case.language}@${self.model_id}"
            file_name = f"{prefix}@{self.config.approach}.txt"
            self.save_output(self.config.output_dir, file_name, summary)

            self.logger.info("Saved output for case %s", case.case_id)
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
