from pathlib import Path
from posixpath import basename
import re

from attr import dataclass
from helpers import Case
from .read_data import read_markdown_file, read_json_file


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


def read_all_cases(base_dir: Path,
                   filter_specialty=None,
                   filter_language=None) -> dict[str, CaseDescAndData]:
    """
    Read all the cases from the given directory.
    """
    raw_ids = [
        re.sub(r'merged_(.*).md', r'\1', basename(f))
        for f in (base_dir / 'merged').glob('*.md')
    ]

    if filter_specialty:
        raw_ids = [
            case_id for case_id in raw_ids
            if case_id.startswith(filter_specialty)
        ]

    if len(raw_ids) == 0:
        raise ValueError(f"No cases found for specialty '{filter_specialty}'")

    if filter_language:
        raw_ids = [
            case_id for case_id in raw_ids if case_id.endswith(filter_language)
        ]

    if len(raw_ids) == 0:
        raise ValueError(f"No cases found for language '{filter_language}'")

    return {
        case_id:
        CaseDescAndData(specialty=re.sub(r'([^_]+)_.*', r'\1', case_id),
                        case_id=re.sub(r'[^_]+_(.*)_.+', r'\1', case_id),
                        language=re.sub(r'.+_([^_]+)$', r'\1', case_id),
                        text=read_markdown_file(base_dir / 'merged' /
                                                f'merged_{case_id}.md'),
                        object=read_json_file(base_dir / 'markdown' /
                                              f'markdown_{case_id}.json'))
        for case_id in raw_ids
    }
