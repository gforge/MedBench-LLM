import re
from collections import defaultdict
from pathlib import Path
from posixpath import basename

from attr import dataclass

from helpers import Case

from .read_data import read_json_file, read_markdown_file


@dataclass
class CaseDescAndData:
    """
    A dataclass that holds the description and data of a case.
    """

    specialty: str
    case_id: str
    language: str
    text: str
    object: Case

    def __repr__(self):
        return f"{self.specialty} - {self.case_id} ({self.language}, len={len(self.text)})"


def read_all_cases(
    base_dir: Path,
    filter_specialty: str | None = None,
    filter_languages: list[str] | None = None,
    require_all_languages_for_case: bool = False,
) -> dict[str, CaseDescAndData]:
    """
    Read all the cases from the given directory.
    """
    raw_ids = [re.sub(r"merged_(.*).md", r"\1", basename(f)) for f in (base_dir / "merged").glob("*.md")]

    case_pattern = re.compile(r"^(?P<specialty>.+)_(?P<case_id>Case \d+)_(?P<language>.+)$")
    parsed: list[tuple[str, str, str, str]] = []
    for raw_id in raw_ids:
        match = case_pattern.match(raw_id)
        if not match:
            continue
        parsed.append(
            (
                raw_id,
                match.group("specialty"),
                match.group("case_id"),
                match.group("language"),
            )
        )

    if filter_specialty:
        parsed = [record for record in parsed if record[1] == filter_specialty]

    if len(parsed) == 0:
        raise ValueError(f"No cases found for specialty '{filter_specialty}'")

    if filter_languages:
        selected_languages = set(filter_languages)
        parsed = [record for record in parsed if record[3] in selected_languages]

        if require_all_languages_for_case and len(selected_languages) > 1:
            languages_by_case: dict[tuple[str, str], set[str]] = defaultdict(set)
            for _, specialty, case_id, language in parsed:
                languages_by_case[(specialty, case_id)].add(language)

            complete_cases = {
                case_key for case_key, languages in languages_by_case.items() if selected_languages.issubset(languages)
            }
            parsed = [record for record in parsed if (record[1], record[2]) in complete_cases]

    if len(parsed) == 0:
        language_text = ", ".join(filter_languages or [])
        raise ValueError(f"No cases found for language selection '{language_text}'")

    raw_ids = [record[0] for record in parsed]

    return {
        case_id: CaseDescAndData(
            specialty=re.sub(r"([^_]+)_.*", r"\1", case_id),
            case_id=re.sub(r"[^_]+_(.*)_.+", r"\1", case_id),
            language=re.sub(r".+_([^_]+)$", r"\1", case_id),
            text=read_markdown_file(base_dir / "merged" / f"merged_{case_id}.md"),
            object=read_json_file(base_dir / "markdown" / f"markdown_{case_id}.json"),
        )
        for case_id in raw_ids
    }
