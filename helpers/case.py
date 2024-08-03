import re
from datetime import datetime, timedelta
from typing import Callable

from .note_section import NoteSection
from .raw_case import RawCase
from .single_day import SingleDay


class Case(RawCase):
    """
    A class representing a case with sections that can be used in different sections
    of the prompts.
    """

    def __init__(self, **data):
        super().__init__(**data)
        self._sections = [
            NoteSection(raw, language=self.language)
            for raw in re.split("(^|\n)# ", self.chart) if raw.strip()
        ]
        assert self._sections, f'No sections found in case: {self.chart}'

        dd: list[SingleDay] = []
        for single_date in self.get_all_dates():
            dd.append(
                SingleDay(
                    date=single_date,
                    language=self.language,
                    notes=[s for s in self._sections if s.date == single_date],
                    medications=[
                        m for m in self.singleMedication
                        if m.date == single_date
                    ],
                    labs=[l for l in self.singleLab if l.date == single_date],
                ))
        self.daily_data = dd

        # Sort sections by date
        self._sections.sort(key=lambda x: x.date)

    def get_all_dates(self) -> list[datetime]:
        """
        Returns a list of all dates in the case,
        note that even dates without notes are included.
        """
        return [
            self.first_date + timedelta(days=i)
            for i in range((self.last_date - self.first_date).days + 1)
        ]

    @property
    def sections(self) -> list[NoteSection]:
        """
        Returns a list of note sections, e..g admission note, surgery note, progress note
        """
        return self._sections

    @property
    def first_date(self) -> datetime:
        """
        Returns the first date of the case
        """
        return min(section.date for section in self.sections)

    @property
    def last_date(self) -> datetime:
        """
        Returns the last date of the case
        """
        return max(section.date for section in self.sections)

    def __extract_progress_notes(self):
        typename: re.Pattern | None = None
        if self.language == "original":
            typename = re.compile(r"Progress")
        else:
            raise ValueError(f"Unsupported language: {self.language}")

        return [
            section for section in self.sections
            if typename.match(section.type)
        ]

    def __extract_progress_note(self, idx: int):
        notes = self.__extract_progress_notes()
        if idx < 0:
            idx = len(notes) + idx
        return notes[idx]

    @property
    def progress_notes(self) -> str:
        """
        Returns a string of all progress notes
        """
        return "\n\n".join(
            [note.to_markdown() for note in self.__extract_progress_notes()])

    def __extract_surgery_notes(self):
        typename: re.Pattern | None = None
        if self.language == "original":
            typename = re.compile(r"^(Operation|Surgery)")
        else:
            raise ValueError(f"Unsupported language: {self.language}")

        return [
            section for section in self.sections
            if typename.match(section.type)
        ]

    def __extract_surgery_note(self, idx: int):
        notes = self.__extract_surgery_notes()
        if idx < 0:
            idx = len(notes) + idx

        return notes[idx]

    @property
    def surgery(self) -> str:
        """
        String of all surgery notes.

        If no surgery notes are found, returns "No surgery notes found"
        """
        notes = self.__extract_surgery_notes()
        if not notes:
            return "No surgery notes found"

        return "\n\n".join([n.to_markdown() for n in notes])

    @property
    def first_day_notes(self) -> str:
        """
        Returns the first day of the case
        """
        return self.daily_data[0].get_note_section()

    @property
    def last_surgery_and_progress_notes(self):
        """
        Returns the last surgery and progress notes
        """
        try:
            last_op_note = self.__extract_surgery_note(-1).to_markdown()
        except IndexError:
            last_op_note = ""

        try:
            last_progress_note = self.__extract_progress_note(-1).to_markdown()
        except IndexError:
            last_progress_note = ""

        return (last_op_note + "\n\n" + last_progress_note).strip()

    def initial_medications(self):
        """
        Returns the initial medications that were given to the patient
        at the date of admission.
        """
        return self.daily_data[0].get_medications_list(include_header=False)

    def initial_lab(self):
        """
        Returns the initial lab tests that were done on the patient
        at the date of admission.
        """
        return self.daily_data[0].get_labs_list(include_header=False)

    @property
    def days(self) -> int:
        """
        Returns the number of days the case spans
        """
        return self.sections[-1].days_between(self.sections[0])

    def get_day(self, day: int | datetime) -> SingleDay:
        """
        Returns a SingleDay object for the specified day
        """
        if isinstance(day, datetime):
            day = self.get_all_dates().index(day)

        day = day - 1  # 0-indexed
        assert day >= 0, "Day should be greater than or equal to 0"
        assert day < self.days, f"Day should be less than {self.days}"
        return self.daily_data[day]

    def get_progress_notes_and_lab(self,
                                   day: int | datetime | None = None) -> str:
        """
        Returns the notes and labs for the specified day
        """
        selected_dates = self.daily_data
        if day is not None:
            selected_dates = [self.get_day(day)]

        note_filter_fn: Callable[[NoteSection],
                                 bool] = lambda d: d.is_progress_note

        return "\n\n".join([
            date.to_markdown(include_meds=False, filter_note_fn=note_filter_fn)
            for date in selected_dates
        ])

    @property
    def all_medications(self) -> str:
        """
        Returns all medications in the case
        """
        return "\n\n".join([
            d.get_medications_list(include_header=True)
            for d in self.daily_data
        ])

    def __rep__(self):
        labs = f'{len(self.singleLab)} labs'
        meds = f'{len(self.singleMedication)} medications'
        notes = f'{len(self.chart)} characters of notes'

        return f"Case({self.id} [{self.specialty} in {self.language}], {labs}, {meds}, {notes})"

    def __str__(self):
        return self.__rep__()
