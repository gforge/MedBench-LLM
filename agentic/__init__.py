"""
Agentic discharge summary generation approaches.

This module implements various agentic architectures for generating
discharge summaries, designed for comparison with basic single-shot approaches.

Architectures:
- reflection: Simple reflection loop with critic and refinement
- hierarchical: Complex multi-agent system with planning and specialization
"""

from .hierarchical import HierarchicalMultiAgent
from .reflection import ReflectionAgent

__all__ = ["ReflectionAgent", "HierarchicalMultiAgent"]
