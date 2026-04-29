"""Configuration management for MedBench LLM evaluation."""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .init_model import AvailableModels, available_models


@dataclass
class EvaluationConfig:
    """Configuration for running LLM evaluation on medical cases.

    Attributes:
        specialty: Medical specialty to filter cases (e.g., "Medicine", "Surgery")
        languages: Language filters for cases (e.g., ["original"], ["Swedish", "English"])
        model_name: Name of the LLM model to use
        temperature: Temperature parameter for LLM generation (0.0 = deterministic)
        rate_limit_seconds: Seconds to wait between API calls to avoid rate limiting
        data_dir: Base directory containing processed case data
        output_dir: Directory to save generated summaries
        approach: Summarization approach to use (e.g., "basic")
        require_complete_language_set: Whether to keep only case IDs present in all selected languages
    """

    specialty: str
    languages: list[str]
    model_name: AvailableModels
    temperature: float
    rate_limit_seconds: int
    data_dir: Path
    output_dir: Path
    approach: str = "basic"
    require_complete_language_set: bool = False

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "EvaluationConfig":
        """Create configuration from parsed command-line arguments.

        Args:
            args: Parsed arguments from argparse

        Returns:
            EvaluationConfig instance
        """
        project_folder = Path.cwd()
        data_dir = project_folder / "data" / "processed"
        output_dir = project_folder / "data" / "output" / args.specialty

        return cls(
            specialty=args.specialty,
            languages=args.languages,
            model_name=args.model,
            temperature=args.temperature,
            rate_limit_seconds=args.rate_limit,
            data_dir=data_dir,
            output_dir=output_dir,
            approach=args.approach,
            require_complete_language_set=args.require_complete_language_set,
        )


CASE_FILE_PATTERN = re.compile(r"^merged_(?P<specialty>.+)_(?P<case_id>Case \d+)_(?P<language>.+)\.md$")
MODEL_CHOICES: tuple[AvailableModels, ...] = tuple(available_models.keys())
APPROACH_CHOICES: tuple[str, ...] = ("basic", "reflection")
COMPLETE_LANGUAGE_CHOICES: tuple[str, ...] = ("auto", "yes", "no")

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_DIM = "\033[2m"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _color(text: str, code: str) -> str:
    if not _supports_color():
        return text
    return f"{code}{text}{ANSI_RESET}"


def _header(text: str) -> str:
    return _color(text, ANSI_BOLD + ANSI_CYAN)


def _option_text(text: str) -> str:
    return _color(text, ANSI_GREEN)


def _hint_text(text: str) -> str:
    return _color(text, ANSI_DIM)


def _prompt_text(text: str) -> str:
    return _color(text, ANSI_BOLD + ANSI_BLUE)


def _warning_text(text: str) -> str:
    return _color(text, ANSI_YELLOW)


def _prompt_for_choice(
    label: str,
    options: Sequence[str],
    descriptions: dict[str, str] | None = None,
) -> str:
    """Prompt the user to choose one option from a numbered list."""
    print(_header(f"Available {label} options:"))
    for index, option in enumerate(options, start=1):
        description = descriptions.get(option) if descriptions else None
        suffix = f" {_hint_text(f'({description})')}" if description else ""
        print(f"{_option_text(str(index) + '.')} {option}{suffix}")

    while True:
        raw_value = input(_prompt_text(f"Select {label} [1-{len(options)}]: ")).strip()
        if not raw_value:
            print(_warning_text("A selection is required."))
            continue

        if raw_value.isdigit():
            selected_index = int(raw_value)
            if 1 <= selected_index <= len(options):
                return options[selected_index - 1]

        if raw_value in options:
            return raw_value

        print(_warning_text(f"Invalid {label} selection: {raw_value}"))


def _format_case_count(case_count: int) -> str:
    suffix = "case" if case_count == 1 else "cases"
    return f"{case_count} {suffix}"


def _parse_case_inventory(base_dir: Path) -> list[tuple[str, str, str]]:
    """Return `(specialty, case_id, language)` triples discovered from processed case files."""
    merged_dir = base_dir / "merged"
    if not merged_dir.exists():
        return []

    inventory: list[tuple[str, str, str]] = []
    for case_file in sorted(merged_dir.glob("merged_*.md")):
        match = CASE_FILE_PATTERN.match(case_file.name)
        if not match:
            continue
        inventory.append(
            (
                match.group("specialty"),
                match.group("case_id"),
                match.group("language"),
            )
        )

    return inventory


def _count_by_key(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _discover_specialties(base_dir: Path) -> dict[str, int]:
    inventory = _parse_case_inventory(base_dir)
    specialty_cases: dict[str, set[str]] = {}
    for specialty, case_id, _ in inventory:
        specialty_cases.setdefault(specialty, set()).add(case_id)
    return {specialty: len(case_ids) for specialty, case_ids in specialty_cases.items()}


def _discover_languages(base_dir: Path, specialty: str) -> dict[str, int]:
    inventory = _parse_case_inventory(base_dir)
    return _count_by_key(language for case_specialty, _, language in inventory if case_specialty == specialty)


def _sort_languages(languages: Iterable[str]) -> list[str]:
    """Sort languages alphabetically, but keep `original` first when present."""
    unique_languages = sorted(set(languages))
    if "original" not in unique_languages:
        return unique_languages
    return ["original"] + [language for language in unique_languages if language != "original"]


def _resolve_specialty(base_dir: Path, specialty: str | None) -> str:
    specialties = _discover_specialties(base_dir)
    if not specialties:
        raise FileNotFoundError(f"No processed cases found in {base_dir / 'merged'}")

    options = sorted(specialties)
    if specialty:
        if specialty not in specialties:
            available = ", ".join(options)
            raise ValueError(f"Unknown specialty '{specialty}'. Available specialties: {available}")
        return specialty

    descriptions = {option: _format_case_count(specialties[option]) for option in options}
    return _prompt_for_choice("specialty", options, descriptions)


def _prompt_for_multi_choice(
    label: str,
    options: Sequence[str],
    descriptions: dict[str, str] | None = None,
) -> list[str]:
    """Prompt the user to choose one or more options from a numbered list."""
    print(_header(f"Available {label} options:"))
    print(f"{_option_text('0.')} all")
    for index, option in enumerate(options, start=1):
        description = descriptions.get(option) if descriptions else None
        suffix = f" {_hint_text(f'({description})')}" if description else ""
        print(f"{_option_text(str(index) + '.')} {option}{suffix}")

    while True:
        raw_value = input(_prompt_text(f"Select {label} (0 for all, comma-separated indices or names): ")).strip()
        if not raw_value:
            print(_warning_text("A selection is required."))
            continue

        if raw_value in {"0", "all", "ALL", "All"}:
            return list(options)

        tokens = [token.strip() for token in raw_value.split(",") if token.strip()]
        if not tokens:
            print(_warning_text("A selection is required."))
            continue

        selected: list[str] = []
        valid = True
        for token in tokens:
            candidate: str | None = None
            if token.isdigit():
                selected_index = int(token)
                if 1 <= selected_index <= len(options):
                    candidate = options[selected_index - 1]
            elif token in options:
                candidate = token

            if not candidate:
                valid = False
                print(_warning_text(f"Invalid {label} selection: {token}"))
                break

            if candidate not in selected:
                selected.append(candidate)

        if valid and selected:
            return selected


def _resolve_languages(base_dir: Path, specialty: str, language_arg: str | None) -> list[str]:
    languages = _discover_languages(base_dir, specialty)
    if not languages:
        raise ValueError(f"No languages found for specialty '{specialty}'")

    options = _sort_languages(languages)

    if language_arg:
        if language_arg.lower() == "all":
            return options

        requested = [token.strip() for token in language_arg.split(",") if token.strip()]
        if not requested:
            raise ValueError("--language was provided but empty")

        unknown = [language for language in requested if language not in languages]
        if unknown:
            available = ", ".join(options)
            unknown_text = ", ".join(unknown)
            raise ValueError(
                f"Unknown language(s) '{unknown_text}' for specialty '{specialty}'. Available languages: {available}"
            )

        # Preserve user order while deduplicating.
        selected: list[str] = []
        for language in requested:
            if language not in selected:
                selected.append(language)
        return selected

    descriptions = {option: _format_case_count(languages[option]) for option in options}
    return _prompt_for_multi_choice("language", options, descriptions)


def _resolve_complete_language_set(
    selected_languages: Sequence[str],
    complete_language_set: str,
    is_language_selection_interactive: bool,
) -> bool:
    """Resolve whether only cases complete across selected languages should be included."""
    if len(selected_languages) <= 1:
        return False

    if complete_language_set == "yes":
        return True
    if complete_language_set == "no":
        return False

    if is_language_selection_interactive:
        prompt = "Require case IDs to exist in all selected languages (recommended for language comparison)? [Y/n]: "
        while True:
            raw_value = input(_prompt_text(prompt)).strip().lower()
            if raw_value in {"", "y", "yes"}:
                return True
            if raw_value in {"n", "no"}:
                return False
            print(_warning_text(f"Invalid selection: {raw_value}"))

    # Auto mode defaults to complete language sets for multi-language runs.
    return True


def _summarize_selected_cases(
    base_dir: Path,
    specialty: str,
    selected_languages: Sequence[str],
    require_complete_language_set: bool,
) -> tuple[list[str], int]:
    """Return selected case IDs and number of case-language records to process."""
    selected_language_set = set(selected_languages)
    inventory = [
        (spec, case_id, language)
        for spec, case_id, language in _parse_case_inventory(base_dir)
        if spec == specialty and language in selected_language_set
    ]

    if require_complete_language_set and len(selected_language_set) > 1:
        languages_by_case: dict[str, set[str]] = {}
        for _, case_id, language in inventory:
            languages_by_case.setdefault(case_id, set()).add(language)

        selected_case_ids = sorted(
            [case_id for case_id, languages in languages_by_case.items() if selected_language_set.issubset(languages)]
        )
        selected_case_id_set = set(selected_case_ids)
        selected_records = [
            (spec, case_id, language) for spec, case_id, language in inventory if case_id in selected_case_id_set
        ]
        return selected_case_ids, len(selected_records)

    selected_case_ids = sorted({case_id for _, case_id, _ in inventory})
    return selected_case_ids, len(inventory)


def _print_case_selection_preview(
    base_dir: Path,
    specialty: str,
    selected_languages: Sequence[str],
    require_complete_language_set: bool,
) -> None:
    """Print a short preview of which cases will be processed."""
    case_ids, record_count = _summarize_selected_cases(
        base_dir=base_dir,
        specialty=specialty,
        selected_languages=selected_languages,
        require_complete_language_set=require_complete_language_set,
    )

    print(_header("Selection preview:"))
    print(f"{_option_text('-')} Specialty: {specialty}")
    print(f"{_option_text('-')} Languages: {', '.join(selected_languages)}")
    print(f"{_option_text('-')} Unique case IDs: {len(case_ids)}")
    print(f"{_option_text('-')} Case-language records to process: {record_count}")

    if len(case_ids) == 0:
        print(_warning_text("No cases match this selection."))
        return

    if len(case_ids) <= 10:
        print(f"{_option_text('-')} Case IDs: {', '.join(case_ids)}")
        return

    print(_hint_text("More than 10 cases selected. Showing summary only."))


def _resolve_model(model: str | None) -> AvailableModels:
    options: Sequence[str] = MODEL_CHOICES
    if model:
        return model  # type: ignore[return-value]
    return _prompt_for_choice("model", options)  # type: ignore[return-value]


def _resolve_approach(approach: str | None) -> str:
    options: Sequence[str] = APPROACH_CHOICES
    if approach:
        return approach
    return _prompt_for_choice("approach", options)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for evaluation configuration.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation on medical case summaries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--specialty",
        type=str,
        help="Medical specialty to filter cases",
    )

    parser.add_argument(
        "--language",
        type=str,
        help="Language filter for cases. Use one value, comma-separated values, or 'all'",
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=MODEL_CHOICES,
        help="LLM model to use for generation",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for LLM generation (0.0 = deterministic, higher = more random)",
    )

    parser.add_argument(
        "--rate-limit",
        type=int,
        default=60,
        help="Seconds to wait between API calls to avoid rate limiting",
    )

    parser.add_argument(
        "--approach",
        type=str,
        choices=APPROACH_CHOICES,
        help="Summarization approach to use",
    )

    parser.add_argument(
        "--require-complete-language-set",
        type=str,
        choices=COMPLETE_LANGUAGE_CHOICES,
        default="auto",
        help="For multi-language selection, keep only case IDs present in all selected languages (yes/no/auto)",
    )

    args = parser.parse_args()

    project_folder = Path.cwd()
    data_dir = project_folder / "data" / "processed"

    args.specialty = _resolve_specialty(data_dir, args.specialty)
    language_was_omitted = args.language is None
    args.languages = _resolve_languages(data_dir, args.specialty, args.language)
    # Keep backward-compatible single-value field for consumers expecting `args.language`.
    args.language = ",".join(args.languages)
    args.require_complete_language_set = _resolve_complete_language_set(
        selected_languages=args.languages,
        complete_language_set=args.require_complete_language_set,
        is_language_selection_interactive=language_was_omitted,
    )
    if language_was_omitted:
        _print_case_selection_preview(
            base_dir=data_dir,
            specialty=args.specialty,
            selected_languages=args.languages,
            require_complete_language_set=args.require_complete_language_set,
        )
    args.model = _resolve_model(args.model)
    args.approach = _resolve_approach(args.approach)

    return args
