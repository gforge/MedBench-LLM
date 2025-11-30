"""Typed result for summarization approaches."""

from typing import Any, Protocol

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from .case import Case


class SummarizeResult(BaseModel):
    """Typed result returned by all summarization approaches.

    This provides a consistent interface for the evaluator to consume,
    regardless of which approach (basic, reflection, hierarchical) is used.
    """

    summary: str
    """The generated discharge summary text."""

    num_api_calls: int = 1
    """Number of API calls made during generation."""

    iterations: int | None = None
    """Number of refinement iterations (for agentic approaches)."""

    extras: dict[str, Any] = Field(default_factory=dict)
    """Additional metadata specific to the approach (e.g., drafts, critiques)."""


class SummarizeFn(Protocol):
    """Protocol defining the signature for all summarization functions.

    All approaches (basic, reflection, hierarchical) should implement this signature.
    """

    def __call__(
        self,
        llm: BaseChatModel,
        language: str,
        case: Case,
    ) -> SummarizeResult:
        """Generate a discharge summary from a case.

        Args:
            llm: The language model instance.
            language: The language for prompts and output.
            case: The Case object containing all clinical data.

        Returns:
            SummarizeResult with the summary and metadata.
        """
