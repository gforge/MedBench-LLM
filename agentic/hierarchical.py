"""
Hierarchical multi-agent discharge summary generation.

This implements a complex agentic architecture with:
1. Orchestrator: Plans decomposition strategy
2. Topic agents: Specialized agents for each diagnosis/topic
3. Relationship mapper: Identifies connections between topics
4. Synthesis agent: Combines sections coherently
5. QA agent: Final validation

Designed to handle complex cases with multiple diagnoses and
long hospital courses.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from helpers import Case


def read_prompt(module: str, prompt_type: str, prompt_name: str, language: str) -> str:
    """
    Helper to read prompts for agentic approaches.

    Args:
        module: Module name (e.g., "agentic") - currently unused
        prompt_type: Type of approach (e.g., "reflection", "hierarchical")
        prompt_name: Name of prompt (e.g., "generator_system")
        language: Language (e.g., "English", "Swedish")

    Returns:
        Prompt content as string
    """
    prompt_path = (
        Path(__file__).parent / "prompts" / language / prompt_type / f"{prompt_name}.md"
    )

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found at {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


@dataclass
class Topic:
    """A clinical topic (diagnosis/problem) identified in the notes."""

    name: str
    category: str  # "main", "secondary", "complication"
    icd10_code: Optional[str]
    complexity: float  # 0-1, determines agent specialization
    key_events: List[str]


@dataclass
class Relationship:
    """Relationship between two topics."""

    topic1: str
    topic2: str
    relationship_type: str  # "causes", "complicates", "concurrent"
    description: str


@dataclass
class ExecutionPlan:
    """Plan created by orchestrator."""

    topics: List[Topic]
    relationships: List[Relationship]
    temporal_order: List[str]  # Order events should be presented
    complexity_score: float
    recommended_strategy: str  # "simple", "decomposed", "specialized"


class HierarchicalMultiAgent:
    """
    Hierarchical multi-agent discharge summary generator.

    Uses multiple specialized agents coordinated by an orchestrator:
    - Orchestrator decides decomposition strategy
    - Topic agents handle specific diagnoses/problems
    - Synthesis agent combines coherently
    - QA agent validates quality
    """

    def __init__(self, model, language: str = "English"):
        """
        Initialize the hierarchical multi-agent system.

        Args:
            model: LLM model instance (from init_model)
            language: "English" or "Swedish"
        """
        self.model = model
        self.language = language

        # Load prompts for each agent
        self.orchestrator_system = read_prompt(
            "agentic", "hierarchical", "orchestrator_system", language
        )
        self.orchestrator_human = read_prompt(
            "agentic", "hierarchical", "orchestrator_human", language
        )

        self.topic_identifier_system = read_prompt(
            "agentic", "hierarchical", "topic_identifier_system", language
        )
        self.topic_identifier_human = read_prompt(
            "agentic", "hierarchical", "topic_identifier_human", language
        )

        self.topic_agent_system = read_prompt(
            "agentic", "hierarchical", "topic_agent_system", language
        )
        self.topic_agent_human = read_prompt(
            "agentic", "hierarchical", "topic_agent_human", language
        )

        self.relationship_system = read_prompt(
            "agentic", "hierarchical", "relationship_system", language
        )
        self.relationship_human = read_prompt(
            "agentic", "hierarchical", "relationship_human", language
        )

        self.synthesis_system = read_prompt(
            "agentic", "hierarchical", "synthesis_system", language
        )
        self.synthesis_human = read_prompt(
            "agentic", "hierarchical", "synthesis_human", language
        )

        self.qa_system = read_prompt("agentic", "hierarchical", "qa_system", language)
        self.qa_human = read_prompt("agentic", "hierarchical", "qa_human", language)

    def generate(self, case: Case) -> Dict:
        """
        Generate discharge summary using hierarchical multi-agent approach.

        Args:
            case: Case object with clinical notes

        Returns:
            Dict with:
                - summary: Final discharge summary
                - plan: Execution plan from orchestrator
                - topic_sections: Individual sections per topic
                - synthesis_steps: Steps in synthesis process
                - qa_report: Quality assurance findings
        """
        notes = case.to_prompt_string()

        # Step 1: Orchestrator creates execution plan
        plan = self._create_plan(notes)

        # Step 2: Identify topics
        topics = self._identify_topics(notes)

        # Step 3: Map relationships
        relationships = self._map_relationships(topics, notes)

        # Step 4: Generate sections per topic
        topic_sections = {}
        for topic in topics:
            section = self._generate_topic_section(topic, notes, relationships)
            topic_sections[topic.name] = section

        # Step 5: Extract structured information (medications, procedures, etc.)
        structured_data = self._extract_structured_data(notes)

        # Step 6: Synthesize into coherent summary
        draft = self._synthesize_summary(
            topic_sections, relationships, structured_data, plan
        )

        # Step 7: Quality assurance
        qa_report = self._quality_assurance(draft, notes)

        # Step 8: Revise if needed
        if not qa_report["acceptable"]:
            draft = self._revise_summary(draft, qa_report, notes)

        return {
            "summary": draft,
            "plan": plan,
            "topics": topics,
            "relationships": relationships,
            "topic_sections": topic_sections,
            "structured_data": structured_data,
            "qa_report": qa_report,
        }

    def _create_plan(self, notes: str) -> ExecutionPlan:
        """Orchestrator analyzes notes and creates execution plan."""
        messages = [
            {"role": "system", "content": self.orchestrator_system},
            {"role": "user", "content": self.orchestrator_human.format(notes=notes)},
        ]
        response = self.model.generate(messages)

        # Parse into ExecutionPlan
        # TODO: Implement structured parsing
        return self._parse_plan(response)

    def _identify_topics(self, notes: str) -> List[Topic]:
        """Identify clinical topics (diagnoses/problems) in notes."""
        messages = [
            {"role": "system", "content": self.topic_identifier_system},
            {
                "role": "user",
                "content": self.topic_identifier_human.format(notes=notes),
            },
        ]
        response = self.model.generate(messages)

        # Parse into Topic objects
        # TODO: Implement structured parsing
        return self._parse_topics(response)

    def _map_relationships(self, topics: List[Topic], notes: str) -> List[Relationship]:
        """Map relationships between topics."""
        topic_summary = "\n".join([f"- {t.name} ({t.category})" for t in topics])

        messages = [
            {"role": "system", "content": self.relationship_system},
            {
                "role": "user",
                "content": self.relationship_human.format(
                    topics=topic_summary, notes=notes
                ),
            },
        ]
        response = self.model.generate(messages)

        # Parse into Relationship objects
        return self._parse_relationships(response)

    def _generate_topic_section(
        self, topic: Topic, notes: str, relationships: List[Relationship]
    ) -> str:
        """Generate section for a specific topic using specialized agent."""
        related = [r for r in relationships if topic.name in [r.topic1, r.topic2]]
        related_summary = "\n".join([f"- {r.description}" for r in related])

        messages = [
            {"role": "system", "content": self.topic_agent_system},
            {
                "role": "user",
                "content": self.topic_agent_human.format(
                    topic=topic.name,
                    category=topic.category,
                    relationships=related_summary,
                    notes=notes,
                ),
            },
        ]
        response = self.model.generate(messages)
        return response

    def _extract_structured_data(self, notes: str) -> Dict:
        """Extract medications, procedures, etc."""
        # TODO: Implement specialized agents for:
        # - Medication reconciliation
        # - Procedure extraction
        # - Follow-up instructions
        return {"medications": {}, "procedures": [], "follow_up": []}

    def _synthesize_summary(
        self,
        topic_sections: Dict[str, str],
        relationships: List[Relationship],
        structured_data: Dict,
        plan: ExecutionPlan,
    ) -> str:
        """Synthesize topic sections into coherent discharge summary."""
        sections_text = "\n\n".join(
            [f"## {topic}\n{content}" for topic, content in topic_sections.items()]
        )

        relationships_text = "\n".join(
            [f"- {r.topic1} → {r.topic2}: {r.description}" for r in relationships]
        )

        messages = [
            {"role": "system", "content": self.synthesis_system},
            {
                "role": "user",
                "content": self.synthesis_human.format(
                    sections=sections_text,
                    relationships=relationships_text,
                    medications=str(structured_data.get("medications", {})),
                    procedures=str(structured_data.get("procedures", [])),
                ),
            },
        ]
        response = self.model.generate(messages)
        return response

    def _quality_assurance(self, draft: str, notes: str) -> Dict:
        """Final quality check."""
        messages = [
            {"role": "system", "content": self.qa_system},
            {"role": "user", "content": self.qa_human.format(draft=draft, notes=notes)},
        ]
        response = self.model.generate(messages)

        # Parse QA report
        return {
            "acceptable": "ACCEPTABLE" in response.upper(),
            "issues": [],
            "feedback": response,
        }

    def _revise_summary(self, draft: str, qa_report: Dict, notes: str) -> str:
        """Revise summary based on QA feedback."""
        # TODO: Implement revision logic
        return draft

    # Helper parsing methods (TODO: Implement properly)
    def _parse_plan(self, text: str) -> ExecutionPlan:
        """Parse orchestrator output into ExecutionPlan."""
        return ExecutionPlan(
            topics=[],
            relationships=[],
            temporal_order=[],
            complexity_score=0.5,
            recommended_strategy="decomposed",
        )

    def _parse_topics(self, text: str) -> List[Topic]:
        """Parse topic identifier output into Topic objects."""
        return []

    def _parse_relationships(self, text: str) -> List[Relationship]:
        """Parse relationship mapper output into Relationship objects."""
        return []
