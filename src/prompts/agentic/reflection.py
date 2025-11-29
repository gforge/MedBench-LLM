"""
Reflection-based agentic discharge summary generation.

This implements a simple agentic architecture with:
1. Generator: Creates initial draft
2. Critic: Evaluates draft quality
3. Refinement: Improves based on critique

Can iterate multiple times until quality threshold met.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from langchain_core.language_models import BaseChatModel

from helpers.case import Case
from helpers.read_prompt import read_single_prompt
from helpers.summarize_result import SummarizeResult


@dataclass
class Critique:
    """Structured critique from the critic agent."""

    completeness_score: float  # 0-1
    accuracy_issues: List[str]
    redundancy_issues: List[str]
    coherence_issues: List[str]
    temporal_issues: List[str]
    is_acceptable: bool
    overall_feedback: str


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

        # Load prompts
        def read_prompt(name: str):
            return read_single_prompt(name, prompt_path=Path("./prompts/agentic/reflection"), language=language)

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
        import logging

        logger = logging.getLogger(__name__)

        # Get notes from Case object - use chart which contains all clinical notes
        notes = case.chart
        logger.info(f"Starting reflection agent for case {case.id}")
        logger.info(f"  Input notes length: {len(notes)} characters")

        # Track all iterations for analysis
        drafts = []
        critiques = []
        api_calls = 0

        # Step 1: Generate initial draft
        logger.info("  [1/3] Generating initial draft...")
        draft = self._generate_draft(notes)
        drafts.append(draft)
        api_calls += 1
        logger.info(f"  ✓ Initial draft generated ({len(draft)} characters)")

        # Step 2-3: Critique and refine loop
        logger.info(f"  [2/3] Starting critique and refinement (max {self.max_iterations} iterations)...")
        for iteration_num in range(self.max_iterations):
            logger.info(f"    Iteration {iteration_num + 1}/{self.max_iterations}: Generating critique...")
            critique = self._critique_draft(draft, notes)
            critiques.append(critique)
            api_calls += 1
            logger.info(f"    ✓ Critique generated - Acceptable: {critique.is_acceptable}")

            # Check if acceptable
            if critique.is_acceptable:
                logger.info(f"  ✓ Draft acceptable after {iteration_num + 1} critique(s)")
                break

            # Refine based on critique
            logger.info(f"    Iteration {iteration_num + 1}/{self.max_iterations}: Refining draft...")
            draft = self._refine_draft(draft, critique, notes)
            drafts.append(draft)
            api_calls += 1
            logger.info(f"    ✓ Draft refined ({len(draft)} characters)")

        logger.info(f"  [3/3] Reflection complete - Total drafts: {len(drafts)}, Total critiques: {len(critiques)}")

        return SummarizeResult(
            summary=draft,
            num_api_calls=api_calls,
            iterations=len(drafts) - 1,  # -1 because first is initial
            extras={
                "critiques": critiques,
                "drafts": drafts,
            },
        )

    def _generate_draft(self, notes: str) -> str:
        """Generate initial draft using basic prompt."""
        import logging

        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        logger = logging.getLogger(__name__)
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
        logger.debug(f"      ← API response received ({len(result)} chars)")
        return str(result)

    def _critique_draft(self, draft: str, notes: str) -> Critique:
        """
        Critique the draft against original notes.

        Returns structured critique for refinement.
        """
        import logging

        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        logger = logging.getLogger(__name__)
        logger.debug("      → API call: Generating critique")

        chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", self.critic_system),
                    ("human", self.critic_human),
                ]
            )
            | self.model
            | StrOutputParser()
        )
        response = chain.invoke({"draft": draft, "notes": notes})
        logger.debug(f"      ← API response received ({len(response)} chars)")

        # Parse structured critique
        # TODO: Implement proper parsing (JSON mode or structured output)
        # For now, return a simple critique object
        return self._parse_critique(response)

    def _refine_draft(self, draft: str, critique: Critique, notes: str) -> str:
        """Refine draft based on critique."""
        import logging

        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        logger = logging.getLogger(__name__)
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
        logger.debug(f"      ← API response received ({len(result)} chars)")
        return str(result)

    def _parse_critique(self, critique_text: str) -> Critique:
        """
        Parse critique text into structured format.

        TODO: Implement robust parsing (use JSON mode or structured output)
        """
        # Placeholder implementation
        # In production, use structured output or careful parsing

        return Critique(
            completeness_score=0.8,
            accuracy_issues=[],
            redundancy_issues=[],
            coherence_issues=[],
            temporal_issues=[],
            is_acceptable="ACCEPTABLE" in critique_text.upper(),
            overall_feedback=critique_text,
        )


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
