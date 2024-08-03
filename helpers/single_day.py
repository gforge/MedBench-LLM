from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Literal

from .note_section import NoteSection
from .raw_case import LabTest, Medication


def to_md_bullet_list(items: list[str]) -> str:
    """
    Converts a list of items into a markdown bullet list.

    Args:
        items (list[str]): The list of items to convert.

    Returns:
        str: The markdown bullet list as a string.
    """
    return "\n".join([f" * {item}" for item in items])


@dataclass
class SingleDay:
    """
    A class representing a single day in a case.
    """
    date: datetime
    language: Literal["original"]
    notes: list[NoteSection]
    medications: list[Medication]
    labs: list[LabTest]

    def __repr__(self):
        return f"SingleDay({self.date_str}, note: {len(self.notes)}, medications: {len(self.medications)}, labs: {len(self.labs)})"

    @property
    def date_str(self):
        """
        Returns the date as a string in the format YYYY-MM-DD
        """
        return self.date.strftime("%Y-%m-%d")

    def get_medications_list(self, include_header: bool = True):
        """
        A markdown bullet list of medications preceded by the # Medications YYYY-MM-DD
        """
        if not self.medications:
            return f"# No medications for {self.date_str}"

        if include_header:
            ret = f"# Medications {self.date_str}\n\n"
        else:
            ret = ""
        return ret + to_md_bullet_list(self.medications)

    def get_labs_list(self, include_header: bool = True):
        """
        A markdown bullet list of lab tests preceded by the header # Labs YYYY-MM-DD HH:mm
        """
        if not self.labs:
            return f"# No labs for {self.date_str}"

        unique_times = sorted(set([lab.time for lab in self.labs]))
        ret = ""

        for time in unique_times:

            if include_header:
                if ret != "":
                    ret += "\n\n"
                ret += f"# Labs {self.date_str} {time}\n\n"

            labs4time = [lab for lab in self.labs if lab.time == time]
            ret += to_md_bullet_list(labs4time)

        return ret

    def get_note_section(self,
                         filter_fn: Callable[[NoteSection], bool]
                         | None = None):
        """
        A markdown section of the note preceded

        Args:
            filter_fn (Callable[[NoteSection], bool]): A function to filter notes.
        """
        notes = self.notes
        if filter_fn:
            notes = [note for note in notes if filter_fn(note)]

        if not notes:
            return f"# No notes for {self.date_str}"

        return "\n\n".join([note.to_markdown() for note in notes])

    def to_markdown(
        self,
        include_notes: bool = True,
        include_meds: bool = True,
        include_lab: bool = True,
        filter_note_fn: Callable[[NoteSection], bool] | None = None,
    ) -> str:
        """
        Returns the single day as a markdown string.

        Args:
            include_notes (bool): Whether to include the notes section.
            include_meds (bool): Whether to include the medications section.
            include_lab (bool): Whether to include the lab section.
            filter_note_fn (Callable[[NoteSection], bool]): A function to filter notes.
        """
        ret = ""
        if include_notes:
            ret += self.get_note_section(filter_note_fn) + "\n\n"

        if include_meds:
            ret += self.get_medications_list(include_header=True) + "\n\n"

        if include_lab:
            ret += self.get_labs_list(include_header=True)

        return ret.strip()
