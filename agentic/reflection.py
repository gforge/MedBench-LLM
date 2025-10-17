"""
Reflection-based agentic discharge summary generation.

This implements a simple agentic architecture with:
1. Generator: Creates initial draft
2. Critic: Evaluates draft quality
3. Refinement: Improves based on critique

Can iterate multiple times until quality threshold met.
"""

from dataclasses import dataclass
from typing import Dict, List

from helpers.case import Case
from helpers.read_prompt import read_prompt


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
        self.generator_system = read_prompt(
            "agentic", "reflection", "generator_system", language
        )
        self.generator_human = read_prompt(
            "agentic", "reflection", "generator_human", language
        )
        self.critic_system = read_prompt(
            "agentic", "reflection", "critic_system", language
        )
        self.critic_human = read_prompt(
            "agentic", "reflection", "critic_human", language
        )
        self.refinement_system = read_prompt(
            "agentic", "reflection", "refinement_system", language
        )
        self.refinement_human = read_prompt(
            "agentic", "reflection", "refinement_human", language
        )

    def generate(self, case: Case) -> Dict:
        """
        Generate discharge summary using reflection loop.

        Args:
            case: Case object with clinical notes

        Returns:
            Dict with:
                - summary: Final discharge summary
                - iterations: Number of iterations performed
                - critiques: List of critiques from each iteration
                - drafts: List of drafts from each iteration
        """
        notes = case.to_prompt_string()

        # Track all iterations for analysis
        drafts = []
        critiques = []

        # Step 1: Generate initial draft
        draft = self._generate_draft(notes)
        drafts.append(draft)

        # Step 2-3: Critique and refine loop
        for iteration in range(self.max_iterations):
            critique = self._critique_draft(draft, notes)
            critiques.append(critique)

            # Check if acceptable
            if critique.is_acceptable:
                break

            # Refine based on critique
            draft = self._refine_draft(draft, critique, notes)
            drafts.append(draft)

        return {
            "summary": draft,
            "iterations": len(drafts) - 1,  # -1 because first is initial
            "critiques": critiques,
            "drafts": drafts,
        }

    def _generate_draft(self, notes: str) -> str:
        """Generate initial draft using basic prompt."""
        messages = [
            {"role": "system", "content": self.generator_system},
            {"role": "user", "content": self.generator_human.format(notes=notes)},
        ]
        response = self.model.generate(messages)
        return response

    def _critique_draft(self, draft: str, notes: str) -> Critique:
        """
        Critique the draft against original notes.

        Returns structured critique for refinement.
        """
        messages = [
            {"role": "system", "content": self.critic_system},
            {
                "role": "user",
                "content": self.critic_human.format(draft=draft, notes=notes),
            },
        ]
        response = self.model.generate(messages)

        # Parse structured critique
        # TODO: Implement proper parsing (JSON mode or structured output)
        # For now, return a simple critique object
        return self._parse_critique(response)

    def _refine_draft(self, draft: str, critique: Critique, notes: str) -> str:
        """Refine draft based on critique."""
        messages = [
            {"role": "system", "content": self.refinement_system},
            {
                "role": "user",
                "content": self.refinement_human.format(
                    draft=draft, critique=critique.overall_feedback, notes=notes
                ),
            },
        ]
        response = self.model.generate(messages)
        return response

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
