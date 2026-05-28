"""Upload LLM-generated summaries to the MedBench Platform.

Scans data/output/{specialty}/Summary_4_*.txt files, maps each to a
chartTranslationId via allData.json, and calls uploadLLMGeneratedSummaries.

Usage:
    python src/upload_summaries.py --url http://localhost:4000 --token <jwt> --specialty Medicine
    python src/upload_summaries.py --url http://localhost:4000 --email admin@x.com --specialty all
    # reads MEDBENCH_DATA_SERVER_API (or MEDBENCH_URL), MEDBENCH_TOKEN
    # or MEDBENCH_EMAIL/MEDBENCH_PASSWORD from env
"""

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from dotenv import load_dotenv

UPLOAD_MUTATION = """
mutation UploadSummaries($summaries: [SummaryInput!]!) {
  uploadLLMGeneratedSummaries(summaries: $summaries) {
    id
    chartTranslationId
    generatedBy
  }
}
"""

LOGIN_MUTATION = """
mutation Login($email: String!, $password: String!) {
  login(email: $email, password: $password) {
    accessToken
  }
}
"""

CHART_SUMMARIES_QUERY = """
query ChartSummaries($id: ID!) {
  chart(id: $id) {
    id
    summaries {
      id
      chartTranslationId
      generatedBy
      generatorType
      createdBy
      createdAt
    }
  }
}
"""

DELETE_SUMMARY_MUTATION = """
mutation DeleteSummary($id: ID!) {
  deleteSummary(id: $id)
}
"""


@dataclass(frozen=True)
class SummaryFile:
    """Metadata parsed from a generated summary file."""

    path: Path
    specialty: str
    case_id: str
    language: str
    generated_by: str
    model_used: str
    prompt_type: str


@dataclass(frozen=True)
class DuplicateSummary:
    """A local upload payload that already exists on the server."""

    local_summary: dict
    server_summary: dict


def graphql_request(url: str, query: str, variables: dict, token: str | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
    if "errors" in body:
        raise RuntimeError(f"GraphQL error: {body['errors']}")
    return body["data"]


def get_token(url: str, email: str, password: str) -> str:
    data = graphql_request(url, LOGIN_MUTATION, {"email": email, "password": password})
    return data["login"]["accessToken"]


def build_chart_index(alldata_path: Path) -> dict[tuple[str, str, str], str]:
    """Return {(specialty, case_id, language): chartTranslationId}."""
    with open(alldata_path, encoding="utf-8") as f:
        cases = json.load(f)
    index: dict[tuple[str, str, str], str] = {}
    for case in cases:
        for chart in case.get("charts", []):
            key = (chart["specialty"], chart["name"], chart["language"])
            index[key] = chart["id"]
    return index


def parse_summary_filename(path: Path, specialty: str = "") -> SummaryFile | None:
    """Parse a summary filename into structured metadata.

    Returns None if the filename does not match the expected pattern.
    """
    name = path.stem  # strip .txt
    if not name.startswith("Summary_4_"):
        return None
    rest = name[len("Summary_4_") :]
    parts = rest.split("@")
    if len(parts) < 3:
        return None
    case_id = parts[0]
    language = parts[1]
    generated_by = "@".join(parts[2:])
    if not generated_by.startswith("$"):
        return None
    generated_parts = generated_by[1:].split("@")
    if len(generated_parts) < 2:
        return None
    prompt_type = generated_parts[-1]
    model_used = "@".join(generated_parts[:-1])
    if not model_used or not prompt_type:
        return None
    return SummaryFile(
        path=path,
        specialty=specialty,
        case_id=case_id,
        language=language,
        generated_by=generated_by,
        model_used=model_used,
        prompt_type=prompt_type,
    )


def _natural_case_key(case_id: str) -> tuple[str, int]:
    prefix, _, suffix = case_id.rpartition(" ")
    if suffix.isdigit():
        return prefix, int(suffix)
    return case_id, 0


def _unique_sorted(values: Iterable[str], *, case_ids: bool = False) -> list[str]:
    unique_values = set(values)
    if case_ids:
        return sorted(unique_values, key=_natural_case_key)
    return sorted(unique_values)


def _format_count(count: int, singular: str, plural: str | None = None) -> str:
    label = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {label}"


def _prompt_for_multi_choice(
    label: str,
    options: Sequence[str],
    descriptions: dict[str, str] | None = None,
) -> list[str]:
    """Prompt the user to choose one or more options from a numbered list."""
    if not options:
        return []

    total_count = _sum_description_counts(options, descriptions)
    total_suffix = f" ({_format_count(total_count, 'summary', 'summaries')})" if total_count is not None else ""
    print(f"\nAvailable {label} options{total_suffix}:")
    print(f"0. all{total_suffix}")
    for index, option in enumerate(options, start=1):
        description = descriptions.get(option) if descriptions else None
        suffix = f" ({description})" if description else ""
        print(f"{index}. {option}{suffix}")

    while True:
        raw_value = input(f"Select {label} (0 for all, comma-separated indices or names): ").strip()
        selected = _resolve_filter_values(raw_value, options)
        if selected:
            return selected
        print(f"Invalid {label} selection: {raw_value}")


def _resolve_filter_values(raw_value: str | None, options: Sequence[str]) -> list[str]:
    """Resolve an argument or prompt value against available options."""
    if raw_value is None:
        return []
    value = raw_value.strip()
    if not value:
        return []
    if value.lower() == "all" or value == "0":
        return list(options)

    selected: list[str] = []
    for token in [part.strip() for part in value.split(",") if part.strip()]:
        candidate: str | None = None
        if token.isdigit():
            selected_index = int(token)
            if 1 <= selected_index <= len(options):
                candidate = options[selected_index - 1]
        elif token in options:
            candidate = token

        if not candidate:
            return []
        if candidate not in selected:
            selected.append(candidate)
    return selected


def _resolve_or_prompt_multi(
    label: str,
    raw_value: str | None,
    options: Sequence[str],
    descriptions: dict[str, str] | None = None,
) -> list[str]:
    if raw_value is None:
        return _prompt_for_multi_choice(label, options, descriptions)

    selected = _resolve_filter_values(raw_value, options)
    if selected:
        return selected

    available = ", ".join(options)
    raise ValueError(f"Unknown {label} selection '{raw_value}'. Available options: {available}")


def _count_by(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _sum_description_counts(options: Sequence[str], descriptions: dict[str, str] | None) -> int | None:
    if not descriptions:
        return None
    total = 0
    for option in options:
        description = descriptions.get(option, "")
        count_text = description.split(" ", 1)[0]
        if not count_text.isdigit():
            return None
        total += int(count_text)
    return total


def _discover_specialties(output_base: Path) -> dict[str, int]:
    specialties: dict[str, int] = {}
    if not output_base.exists():
        return specialties
    for output_dir in sorted(output_base.iterdir()):
        if not output_dir.is_dir():
            continue
        count = len(list(output_dir.glob("Summary_4_*.txt")))
        if count:
            specialties[output_dir.name] = count
    return specialties


def discover_summary_files(output_base: Path, specialties: Sequence[str]) -> list[SummaryFile]:
    """Return parsed generated summary files in the selected specialties."""
    summaries: list[SummaryFile] = []
    for specialty in specialties:
        output_dir = output_base / specialty
        if not output_dir.exists():
            print(f"[{specialty}] Output directory not found, skipping.")
            continue
        for txt_file in sorted(output_dir.glob("Summary_4_*.txt")):
            parsed = parse_summary_filename(txt_file, specialty=specialty)
            if not parsed:
                print(f"  [skip] Unrecognised filename: {txt_file.name}")
                continue
            summaries.append(parsed)
    return summaries


def _filter_summaries(summaries: Sequence[SummaryFile], predicate: Callable[[SummaryFile], bool]) -> list[SummaryFile]:
    return [summary for summary in summaries if predicate(summary)]


def resolve_upload_selection(
    output_base: Path,
    specialty_arg: str | None,
    model_arg: str | None,
    language_arg: str | None,
    prompt_type_arg: str | None,
    case_arg: str | None,
) -> list[SummaryFile]:
    """Resolve CLI and interactive filters to the summaries selected for upload."""
    specialty_counts = _discover_specialties(output_base)
    if not specialty_counts:
        raise FileNotFoundError(f"No generated summaries found in {output_base}")

    specialty_options = sorted(specialty_counts)
    specialty_descriptions = {
        specialty: _format_count(count, "summary", "summaries") for specialty, count in specialty_counts.items()
    }
    specialties = _resolve_or_prompt_multi("specialty", specialty_arg, specialty_options, specialty_descriptions)

    summaries = discover_summary_files(output_base, specialties)
    if not summaries:
        return []

    model_options = _unique_sorted(summary.model_used for summary in summaries)
    model_counts = _count_by(summary.model_used for summary in summaries)
    models = _resolve_or_prompt_multi(
        "model",
        model_arg,
        model_options,
        {model: _format_count(model_counts[model], "summary", "summaries") for model in model_options},
    )
    summaries = _filter_summaries(summaries, lambda summary: summary.model_used in models)

    language_options = _unique_sorted(summary.language for summary in summaries)
    language_counts = _count_by(summary.language for summary in summaries)
    languages = _resolve_or_prompt_multi(
        "language",
        language_arg,
        language_options,
        {language: _format_count(language_counts[language], "summary", "summaries") for language in language_options},
    )
    summaries = _filter_summaries(summaries, lambda summary: summary.language in languages)

    prompt_type_options = _unique_sorted(summary.prompt_type for summary in summaries)
    prompt_type_counts = _count_by(summary.prompt_type for summary in summaries)
    prompt_types = _resolve_or_prompt_multi(
        "prompt type",
        prompt_type_arg,
        prompt_type_options,
        {
            prompt_type: _format_count(prompt_type_counts[prompt_type], "summary", "summaries")
            for prompt_type in prompt_type_options
        },
    )
    summaries = _filter_summaries(summaries, lambda summary: summary.prompt_type in prompt_types)

    case_options = _unique_sorted((summary.case_id for summary in summaries), case_ids=True)
    case_counts = _count_by(summary.case_id for summary in summaries)
    case_ids = _resolve_or_prompt_multi(
        "case",
        case_arg,
        case_options,
        {case_id: _format_count(case_counts[case_id], "summary", "summaries") for case_id in case_options},
    )
    return _filter_summaries(summaries, lambda summary: summary.case_id in case_ids)


def print_selection_preview(summaries: Sequence[SummaryFile]) -> None:
    """Print the selected upload inventory before sending it to the API."""
    specialties = _unique_sorted(summary.specialty for summary in summaries)
    models = _unique_sorted(summary.model_used for summary in summaries)
    languages = _unique_sorted(summary.language for summary in summaries)
    prompt_types = _unique_sorted(summary.prompt_type for summary in summaries)
    case_ids = _unique_sorted((summary.case_id for summary in summaries), case_ids=True)

    print("\nSelection preview:")
    print(f"- Specialties: {', '.join(specialties)}")
    print(f"- Models: {', '.join(models)}")
    print(f"- Languages: {', '.join(languages)}")
    print(f"- Prompt types: {', '.join(prompt_types)}")
    print(f"- Unique case IDs: {len(case_ids)}")
    print(f"- Summaries to upload: {len(summaries)}")
    if len(case_ids) <= 10:
        print(f"- Case IDs: {', '.join(case_ids)}")


def collect_summaries(selected_files: Sequence[SummaryFile], chart_index: dict) -> dict[str, list[dict]]:
    skipped = []
    summaries_by_specialty: dict[str, list[dict]] = {}
    for summary_file in selected_files:
        key = (summary_file.specialty, summary_file.case_id, summary_file.language)
        chart_id = chart_index.get(key)
        if not chart_id:
            skipped.append(f"  [skip] No chartTranslationId for {key}")
            continue
        text = summary_file.path.read_text(encoding="utf-8").strip()
        if len(text) < 50:
            skipped.append(f"  [skip] Text too short (<50 chars): {summary_file.path.name}")
            continue
        summaries_by_specialty.setdefault(summary_file.specialty, []).append(
            {"chartTranslationId": chart_id, "generatedBy": summary_file.generated_by, "text": text}
        )
    for msg in skipped:
        print(msg)
    return summaries_by_specialty


def _summary_key(summary: dict) -> tuple[str, str]:
    return summary["chartTranslationId"], summary["generatedBy"]


def _find_local_duplicate_keys(summaries_by_specialty: dict[str, list[dict]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for summaries in summaries_by_specialty.values():
        for summary in summaries:
            key = _summary_key(summary)
            if key in seen:
                duplicates.add(key)
            seen.add(key)
    return sorted(duplicates)


def _fetch_existing_summary_index(
    url: str, token: str, chart_translation_ids: Sequence[str]
) -> dict[tuple[str, str], dict]:
    existing: dict[tuple[str, str], dict] = {}
    for chart_id in sorted(set(chart_translation_ids)):
        result = graphql_request(url, CHART_SUMMARIES_QUERY, {"id": chart_id}, token=token)
        for summary in result["chart"]["summaries"]:
            if summary.get("generatorType") != "LLM":
                continue
            existing[(summary["chartTranslationId"], summary["generatedBy"])] = summary
    return existing


def _find_server_duplicates(
    summaries_by_specialty: dict[str, list[dict]], existing_summary_index: dict[tuple[str, str], dict]
) -> list[DuplicateSummary]:
    duplicates: list[DuplicateSummary] = []
    for summaries in summaries_by_specialty.values():
        for summary in summaries:
            server_summary = existing_summary_index.get(_summary_key(summary))
            if server_summary:
                duplicates.append(DuplicateSummary(local_summary=summary, server_summary=server_summary))
    return duplicates


def print_duplicate_preview(duplicates: Sequence[DuplicateSummary], *, max_examples: int = 5) -> None:
    print(f"\nFound {len(duplicates)} already-uploaded summaries on the server.")
    for duplicate in duplicates[:max_examples]:
        server_summary = duplicate.server_summary
        print(
            "  "
            f"[duplicate] chartTranslationId={server_summary['chartTranslationId']}, "
            f"generatedBy={server_summary['generatedBy']}, id={server_summary['id']}"
        )
    remaining = len(duplicates) - max_examples
    if remaining > 0:
        print(f"  ... and {remaining} more.")


def resolve_duplicate_action(action: str) -> str:
    if action != "prompt":
        return action
    if not sys.stdin.isatty():
        print("Duplicate action 'prompt' requested in a non-interactive shell; using 'skip'.")
        return "skip"

    options = {
        "s": "skip",
        "skip": "skip",
        "a": "abort",
        "abort": "abort",
        "r": "replace",
        "replace": "replace",
    }
    while True:
        raw_value = input("Handle duplicates: [s]kip, [a]bort, [r]eplace? ").strip().lower()
        if raw_value in options:
            return options[raw_value]
        print("Invalid duplicate action. Choose skip, abort, or replace.")


def delete_duplicate_summaries(url: str, token: str, duplicates: Sequence[DuplicateSummary]) -> int:
    deleted_ids: set[str] = set()
    for duplicate in duplicates:
        summary_id = duplicate.server_summary["id"]
        if summary_id in deleted_ids:
            continue
        graphql_request(url, DELETE_SUMMARY_MUTATION, {"id": summary_id}, token=token)
        deleted_ids.add(summary_id)
    return len(deleted_ids)


def filter_duplicate_summaries(
    summaries_by_specialty: dict[str, list[dict]], duplicates: Sequence[DuplicateSummary]
) -> dict[str, list[dict]]:
    duplicate_keys = {_summary_key(duplicate.local_summary) for duplicate in duplicates}
    filtered: dict[str, list[dict]] = {}
    for specialty, summaries in summaries_by_specialty.items():
        filtered[specialty] = [summary for summary in summaries if _summary_key(summary) not in duplicate_keys]
    return filtered


def preflight_duplicate_summaries(
    url: str,
    token: str,
    summaries_by_specialty: dict[str, list[dict]],
    duplicate_action: str,
) -> dict[str, list[dict]]:
    local_duplicates = _find_local_duplicate_keys(summaries_by_specialty)
    if local_duplicates:
        examples = ", ".join(
            f"(chartTranslationId={chart_id}, generatedBy={generated_by})"
            for chart_id, generated_by in local_duplicates[:5]
        )
        raise RuntimeError(f"Selected local files contain duplicate upload keys. Examples: {examples}")

    chart_translation_ids = [
        summary["chartTranslationId"] for summaries in summaries_by_specialty.values() for summary in summaries
    ]
    if not chart_translation_ids:
        return summaries_by_specialty

    existing_summary_index = _fetch_existing_summary_index(url, token, chart_translation_ids)
    duplicates = _find_server_duplicates(summaries_by_specialty, existing_summary_index)
    if not duplicates:
        return summaries_by_specialty

    print_duplicate_preview(duplicates)
    action = resolve_duplicate_action(duplicate_action)
    if action == "abort":
        raise RuntimeError("Aborting because selected summaries already exist on the server.")
    if action == "replace":
        deleted = delete_duplicate_summaries(url, token, duplicates)
        print(f"Deleted {deleted} already-uploaded summaries before re-upload.")
        return summaries_by_specialty

    filtered = filter_duplicate_summaries(summaries_by_specialty, duplicates)
    skipped = sum(len(summaries) for summaries in summaries_by_specialty.values()) - sum(
        len(summaries) for summaries in filtered.values()
    )
    print(f"Skipping {skipped} already-uploaded summaries.")
    return filtered


def upload_in_batches(url: str, token: str, summaries: list[dict], batch_size: int = 50) -> int:
    uploaded = 0
    for i in range(0, len(summaries), batch_size):
        batch = summaries[i : i + batch_size]
        result = graphql_request(url, UPLOAD_MUTATION, {"summaries": batch}, token=token)
        uploaded += len(result["uploadLLMGeneratedSummaries"])
        print(f"  Uploaded batch {i // batch_size + 1}: {len(batch)} summaries")
    return uploaded


def resolve_token(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    """Resolve authentication before upload selection starts."""
    if args.token:
        return args.token

    if not args.email:
        if not sys.stdin.isatty():
            parser.error("Provide --token or --email (or set MEDBENCH_TOKEN / MEDBENCH_EMAIL env vars)")
        args.email = input("Email for MedBench login: ").strip()

    if not args.email:
        parser.error("Provide --token or --email (or set MEDBENCH_TOKEN / MEDBENCH_EMAIL env vars)")

    if not args.password:
        args.password = getpass.getpass(f"Password for {args.email}: ")

    print(f"Logging in as {args.email}...")
    token = get_token(args.url, args.email, args.password)
    print("Login successful.")
    return token


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Upload LLM summaries to MedBench Platform")
    parser.add_argument(
        "--url",
        default=os.environ.get("MEDBENCH_DATA_SERVER_API")
        or os.environ.get("MEDBENCH_URL", "http://localhost:4000/graphql"),
    )
    parser.add_argument("--token", default=os.environ.get("MEDBENCH_TOKEN"))
    parser.add_argument("--email", default=os.environ.get("MEDBENCH_EMAIL"))
    parser.add_argument(
        "--password",
        default=os.environ.get("MEDBENCH_PASSWORD"),
        help="Password for login; if omitted the script prompts securely when --email is provided",
    )
    parser.add_argument(
        "--specialty",
        help="Specialty subfolder selection. Use one value, comma-separated values, or 'all'",
    )
    parser.add_argument(
        "--model",
        help="Model metadata filter from generated summary filenames. Use one value, comma-separated values, or 'all'",
    )
    parser.add_argument(
        "--language",
        help="Language filter from generated summary filenames. Use one value, comma-separated values, or 'all'",
    )
    parser.add_argument(
        "--approach",
        dest="prompt_type",
        help="Prompt type / summarization approach filter. Use one value, comma-separated values, or 'all'",
    )
    parser.add_argument(
        "--prompt-type",
        dest="prompt_type",
        help="Alias for --approach",
    )
    parser.add_argument(
        "--case",
        dest="case_ids",
        help="Case ID filter. Use one value, comma-separated values, or 'all'",
    )
    parser.add_argument(
        "--alldata",
        default=str(Path(__file__).parent.parent / "data" / "output" / "allData.json"),
        help="Path to allData.json exported from the Platform",
    )
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument(
        "--duplicate-action",
        choices=("skip", "abort", "replace", "prompt"),
        default="prompt" if sys.stdin.isatty() else "skip",
        help=(
            "How to handle summaries already uploaded to the server. "
            "Defaults to prompt in interactive shells and skip otherwise."
        ),
    )
    args = parser.parse_args()

    alldata_path = Path(args.alldata)
    if not alldata_path.exists():
        parser.error(f"allData.json not found at {alldata_path}. Run download_platform_charts.py first.")

    print(f"Loading chart index from {alldata_path}...")
    chart_index = build_chart_index(alldata_path)
    print(f"Loaded {len(chart_index)} chart translations.")

    token = resolve_token(args, parser)

    output_base = Path(__file__).parent.parent / "data" / "output"
    try:
        selected_files = resolve_upload_selection(
            output_base=output_base,
            specialty_arg=args.specialty,
            model_arg=args.model,
            language_arg=args.language,
            prompt_type_arg=args.prompt_type,
            case_arg=args.case_ids,
        )
    except (FileNotFoundError, ValueError) as e:
        parser.error(str(e))

    if not selected_files:
        print("No summaries match this selection.")
        return

    print_selection_preview(selected_files)

    summaries_by_specialty = collect_summaries(selected_files, chart_index)
    try:
        summaries_by_specialty = preflight_duplicate_summaries(
            args.url,
            token,
            summaries_by_specialty,
            duplicate_action=args.duplicate_action,
        )
    except RuntimeError as e:
        parser.error(str(e))

    total_uploaded = 0
    for specialty in sorted({summary.specialty for summary in selected_files}):
        summaries = summaries_by_specialty.get(specialty, [])
        if not summaries:
            print(f"[{specialty}] No uploadable summaries found.")
            continue
        print(f"[{specialty}] Uploading {len(summaries)} summaries...")
        n = upload_in_batches(args.url, token, summaries, batch_size=args.batch_size)
        total_uploaded += n
        print(f"[{specialty}] Done: {n} uploaded.")

    if total_uploaded == 0:
        print("\nNo new summaries to upload.")
        return

    print(f"\nTotal uploaded: {total_uploaded}")


if __name__ == "__main__":
    main()
