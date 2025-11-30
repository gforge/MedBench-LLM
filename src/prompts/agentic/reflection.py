"""
Reflection-based agentic discharge summary generation.

This implements a simple agentic architecture with:
1. Generator: Creates initial draft
2. Critic: Evaluates draft quality
3. Refinement: Improves based on critique

Can iterate multiple times until quality threshold met.
"""

import logging
from pathlib import Path
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from helpers.case import Case
from helpers.summarize_result import SummarizeResult

logger = logging.getLogger(__name__)


class Critique(BaseModel):
    """Structured critique from the critic agent."""

    completeness_score: float = Field(ge=0, le=1, description="Score from 0-1 indicating completeness")
    accuracy_issues: List[str] = Field(default_factory=list, description="List of accuracy problems found")
    redundancy_issues: List[str] = Field(default_factory=list, description="List of redundant information")
    coherence_issues: List[str] = Field(default_factory=list, description="List of coherence/flow problems")
    temporal_issues: List[str] = Field(default_factory=list, description="List of timeline/chronology issues")
    is_acceptable: bool = Field(description="Whether the draft meets quality standards")
    overall_feedback: str = Field(description="Summary feedback for refinement")


class ReflectionAgent:
    """
    Reflection-based agentic discharge summary generator.

    Uses a three-step process:
    1. Generate initial draft using basic prompt
    2. Critique the draft
    3. Refine based on critique

    Can iterate multiple times for improvement.
    """

    def __init__(self, model, language: str = "English", max_iterations: int = 2):
        """
        Initialize the reflection agent.

        Args:
            model: LLM model instance (from init_model)
            language: "English" or "Swedish"
            max_iterations: Maximum number of refinement iterations
        """
        self.model = model
        self.language = language
        self.max_iterations = max_iterations

        # Load prompts - need to include 'reflection' subdirectory in the path
        prompt_base = Path(__file__).parent / "prompts"

        def read_prompt(name: str) -> str:
            # Prompts are in prompts/<Language>/reflection/<name>.md
            lang_dir = language if language.lower() != "original" else "English"
            prompt_file = prompt_base / lang_dir / "reflection" / (name + ".md")
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt not found: {prompt_file}")
            return prompt_file.read_text(encoding="utf-8")

        self.generator_system = read_prompt("generator_system")
        self.generator_human = read_prompt("generator_human")
        self.critic_system = read_prompt("critic_system")
        self.critic_human = read_prompt("critic_human")
        self.refinement_system = read_prompt("refinement_system")
        self.refinement_human = read_prompt("refinement_human")

    def generate(self, case: Case) -> SummarizeResult:
        """
        Generate discharge summary using reflection loop.

        Args:
            case: Case object with clinical notes

        Returns:
            SummarizeResult with summary and metadata.
        """
        # Get notes from Case object - use chart which contains all clinical notes
        notes = case.chart
        logger.info("Starting reflection agent for case %s", case.id)
        logger.info("  Input notes length: %d characters", len(notes))

        # Track all iterations for analysis
        drafts = []
        critiques = []
        api_calls = 0

        # Step 1: Generate initial draft
        logger.info("  [1/3] Generating initial draft...")
        draft = self._generate_draft(notes)
        drafts.append(draft)
        api_calls += 1
        logger.info("  ✓ Initial draft generated (%d characters)", len(draft))

        # Step 2-3: Critique and refine loop
        logger.info("  [2/3] Starting critique and refinement (max %d iterations)...", self.max_iterations)
        for iteration_num in range(self.max_iterations):
            logger.info("    Iteration %d/%d: Generating critique...", iteration_num + 1, self.max_iterations)
            critique = self._critique_draft(draft, notes)
            critiques.append(critique)
            api_calls += 1
            logger.info("    ✓ Critique generated - Acceptable: %s", critique.is_acceptable)

            # Check if acceptable
            if critique.is_acceptable:
                logger.info("  ✓ Draft acceptable after %d critique(s)", iteration_num + 1)
                break

            # Refine based on critique
            logger.info("    Iteration %d/%d: Refining draft...", iteration_num + 1, self.max_iterations)
            draft = self._refine_draft(draft, critique, notes)
            drafts.append(draft)
            api_calls += 1
            logger.info("    ✓ Draft refined (%d characters)", len(draft))

        logger.info("  [3/3] Reflection complete - Total drafts: %d, Total critiques: %d", len(drafts), len(critiques))

        return SummarizeResult(
            summary=draft,
            num_api_calls=api_calls,
            iterations=len(drafts) - 1,  # -1 because first is initial
            extras={
                "critiques": [c.model_dump() for c in critiques],
                "drafts": drafts,
            },
        )

    def _generate_draft(self, notes: str) -> str:
        """Generate initial draft using basic prompt."""
        logger.debug("      → API call: Generating draft")

        chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", self.generator_system),
                    ("human", self.generator_human),
                ]
            )
            | self.model
            | StrOutputParser()
        )
        result = chain.invoke({"notes": notes})
        logger.debug("      ← API response received (%d chars)", len(result))
        return str(result)

    def _critique_draft(self, draft: str, notes: str) -> Critique:
        """
        Critique the draft against original notes.

        Uses structured output to get a properly formatted Critique object.
        """
        logger.debug("      → API call: Generating critique")

        # Use structured output for reliable parsing
        structured_model = self.model.with_structured_output(Critique)
        chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", self.critic_system),
                    ("human", self.critic_human),
                ]
            )
            | structured_model
        )
        result = chain.invoke({"draft": draft, "notes": notes})
        # Cast since with_structured_output returns Any
        critique = Critique.model_validate(result) if isinstance(result, dict) else result
        logger.debug("      ← API response received (acceptable: %s)", critique.is_acceptable)
        return critique

    def _refine_draft(self, draft: str, critique: Critique, notes: str) -> str:
        """Refine draft based on critique."""
        logger.debug("      → API call: Refining draft")

        chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", self.refinement_system),
                    ("human", self.refinement_human),
                ]
            )
            | self.model
            | StrOutputParser()
        )
        result = chain.invoke({"draft": draft, "critique": critique.overall_feedback, "notes": notes})
        logger.debug("      ← API response received (%d chars)", len(result))
        return str(result)


def summarize(llm: BaseChatModel, language: str, case: Case, max_iterations: int = 2) -> SummarizeResult:
    """Generate a summary using the reflection approach.

    Args:
        llm: The language model instance.
        language: The language for prompts and output.
        case: The Case object containing all clinical data.
        max_iterations: Maximum refinement iterations (default: 2).

    Returns:
        SummarizeResult with the summary and metadata.
    """
    agent = ReflectionAgent(model=llm, language=language, max_iterations=max_iterations)
    return agent.generate(case)
