from importlib import import_module
from typing import Any

_EXPORTS = {
    "Case": ".case",
    "EvaluationConfig": ".config",
    "parse_args": ".config",
    "CaseEvaluator": ".evaluator",
    "count_tokens": ".init_model",
    "init_model": ".init_model",
    "validate_model_setup": ".init_model",
    "LabTest": ".lab_tests",
    "Medication": ".medications",
    "NoteSection": ".note_section",
    "RateLimiter": ".rate_limiter",
    "CaseDescAndData": ".read_all_cases",
    "read_all_cases": ".read_all_cases",
    "read_json_file": ".read_data",
    "read_markdown_file": ".read_data",
    "read_dual_prompt": ".read_prompt",
    "read_single_prompt": ".read_prompt",
    "strip_delimeters": ".strip_delimeters",
    "SummarizeFn": ".summarize_result",
    "SummarizeResult": ".summarize_result",
    "Language": ".types",
    "Style": ".types",
    "parse_language_input": ".types",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
