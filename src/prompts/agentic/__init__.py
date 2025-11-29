"""
Agentic discharge summary generation approaches.

This module implements various agentic architectures for generating
discharge summaries, designed for comparison with basic single-shot approaches.

Architectures:
- reflection: Simple reflection loop with critic and refinement
- hierarchical: Complex multi-agent system with planning and specialization
"""

from .reflection import ReflectionAgent

# Hierarchical is under development, only import when needed
# from .hierarchical import HierarchicalMultiAgent

__all__ = ["ReflectionAgent"]
