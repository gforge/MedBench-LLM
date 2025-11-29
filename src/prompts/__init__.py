"""Top-level prompts package.

This package exposes the prompt-driven modules (basic, agentic) used
by the evaluation scripts. Having an __init__.py here avoids module
name ambiguity when tools like mypy inspect both the source tree and
an installed editable package.

Keep this module minimal — subpackages are imported explicitly where
needed to avoid heavy runtime cost during tooling.
"""

__all__ = ["basic", "agentic"]
