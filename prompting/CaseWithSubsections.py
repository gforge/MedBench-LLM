from datetime import date, timedelta
import re

from .NoteSection import NoteSection
from .Case import Case, LabTest, Medication


class CaseWithSubsections():
    """
    A class representing a case with subsections.

    This class extends the base `Case` class and provides additional functionality
    for working with sections within a case.

    Attributes:
        case (Case): The original case object.
        sections (list[NoteSection]): A list of NoteSection objects representing the sections in the case.

    """

    def __init__(self, case: Case):
        self.case = case
        self.sections = [
            NoteSection(raw) for raw in re.split("(^|\n)# ", self.case.chart)
            if len(raw.strip()) > 0
        ]
        assert len(
            self.sections) > 0, f'No sections found in case: {self.case.chart}'

    @property
    def __progress_notes(self):
        return [
            section.raw for section in self.sections
            if section.type == "Progress"
        ]

    @property
    def progress(self):
        return "\n\n".join(self.__progress_notes)

    @property
    def __surgery_notes(self):
        return [
            section.raw for section in self.sections
            if section.type.startswith("Operation")
            or section.type.startswith("Surgery")
        ]

    @property
    def surgery(self):
        return "\n\n".join(self.__surgery_notes)

    @property
    def first_day(self):
        return self.sections[0].raw

    @property
    def last_surgery_and_progress_notes(self):
        last_op_note = self.__surgery_notes[-1] if self.__surgery_notes else ""
        last_progress_note = self.__progress_notes[
            -1] if self.__progress_notes else ""
        return (last_op_note + "\n\n" + last_progress_note).strip()

    @property
    def chart(self):
        return self.case.chart

    @property
    def medications(self):
        return self.case.medications

    def initial_medications(self):
        first_date = self.sections[0].date
        first_medications = [
            med for med in self.case.singleMedication if med.date == first_date
        ]
        # Merge into a single string
        return "\n\n".join([str(med) for med in first_medications])

    @property
    def lab(self):
        return self.case.lab

    def initial_lab(self):
        first_date = self.sections[0].date
        first_labs = [
            lab for lab in self.case.singleLab if lab.date == first_date
        ]
        # Merge into a single string
        return "\n\n".join([str(lab) for lab in first_labs])

    @property
    def days(self) -> int:
        return self.sections[-1].days_between(self.sections[0])

    def __get_section(self, date: date) -> NoteSection | None:
        for section in self.sections:
            if section.date == date:
                return section
        return None

    def __get_medications(self, date: date) -> list[Medication]:
        return [med for med in self.case.singleMedication if med.date == date]

    def __get_lab_tests(self, date: date) -> list[LabTest]:
        return [lab for lab in self.case.singleLab if lab.date == date]

    def get_day(self, day: int) -> str:
        day = day - 1  # 0-indexed
        assert day >= 0, "Day should be greater than or equal to 0"
        assert day < self.days, f"Day should be less than {self.days}"
        date = self.sections[0].date + timedelta(days=day)

        # Find the note
        section = self.__get_section(date)
        medications = self.__get_medications(date)
        labs = self.__get_lab_tests(date)

        # TODO: Add language support
        ret = ""
        if section:
            ret = section.raw
        else:
            ret = f"Day {day} - No notes"

        if len(medications) > 0:
            ret += "\n\n - " + "\n - ".join([str(med) for med in medications])
        else:
            ret += f'\n\n# No medications on {date}'

        if len(labs) > 0:
            ret += "\n\n - " + "\n - ".join([str(lab) for lab in labs])
        else:
            ret += f'\n\n# No labs on {date}'

        return ret

    def __repr__(self):
        sections = f'sections: {len(self.sections)}'
        return f"CaseWithSubsections({self.case.id} [{self.case.language}], {sections}, days: {self.days})"
