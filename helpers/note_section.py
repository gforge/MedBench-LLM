import re
from datetime import datetime


class NoteSection:
    """
    Represents a note section with type, date, time, author, content, and raw data.

    Attributes:
        type (str): The type of the note.
        date (datetime): The date of the note.
        time (str): The time of the note in the format 'HH:MM'.
        author (str): The author of the note.
        content (str): The content of the note.
        raw (str): The raw data of the note.

    Methods:
        __init__(raw: str): Initializes a new instance of the NoteSection class.
        days_between(other: 'NoteSection') -> int: Returns the number of days between the dates of two notes.
        __repr__() -> str: Returns a string representation of the NoteSection.
        to_markdown() -> str: Returns the note section as a markdown string.
    """

    def __init__(self, raw: str, language: str) -> None:
        """
        Initializes a new instance of the NoteSection class.

        Args:
            raw (str): The raw data of the note.

        Raises:
            ValueError: If the first line does not have the correct format or required fields are invalid.
        """
        self.language = language
        self.raw = raw.strip()
        self.type, self.date, self.time, self.author, self.content = self._parse_raw(
            raw)

    def _parse_raw(self, raw: str):
        lines = raw.strip().split("\n")

        # Extract and validate header
        note_type, date, time, author = self._parse_header(lines[0])

        # Process and format content
        content = self._process_content(lines[1:])

        return note_type, date, time, author, content

    def _parse_header(self, header: str):
        """
        Parses and validates the header line.

        Args:
            header (str): The header line to parse.

        Returns:
            tuple: Parsed note type, date, time, and author.

        Raises:
            ValueError: If the header format is invalid.
        """
        pattern = re.compile(
            r"^([^,]+), (\d{4}-\d{2}-\d{2}), (\d{2}:\d{2}), (.+)$")
        match = pattern.match(header)
        if not match:
            raise ValueError(f"Invalid note header format: '{header}'")

        note_type = match.group(1).strip()
        date_str = match.group(2).strip()
        time_str = match.group(3).strip()
        author = match.group(4).strip()

        self._validate_header(note_type, date_str, time_str, author)

        date = datetime.strptime(date_str, "%Y-%m-%d")
        return note_type, date, time_str, author

    def _validate_header(self, note_type: str, date: str, time: str,
                         author: str):
        """
        Validates the header fields.

        Args:
            note_type (str): The type of the note.
            date (str): The date of the note.
            time (str): The time of the note.
            author (str): The author of the note.

        Raises:
            ValueError: If any field is invalid.
        """
        if not note_type:
            raise ValueError("Note type should not be empty")
        if not re.match(r"\d{4}-\d{2}-\d{2}", date):
            raise ValueError("Date should be in YYYY-MM-DD format")
        if not re.match(r"\d{2}:\d{2}", time):
            raise ValueError("Time should be in HH:MM format")
        if not author:
            raise ValueError("Author should not be empty")

    def _process_content(self, content_lines):
        """
        Processes and formats the content lines.

        Args:
            content_lines (list): The lines of content.

        Returns:
            str: The formatted content.
        """
        content_has_header1 = any(
            line.startswith("# ") for line in content_lines)
        if content_has_header1:
            content_lines = [
                f"#{line}" if line.startswith("# ") else line
                for line in content_lines
            ]
        return "\n".join(content_lines)

    def days_between(self, other: 'NoteSection') -> int:
        """
        Returns the number of days between the date of this note and the date of another note.

        Args:
            other (NoteSection): The other note to compare dates with.

        Returns:
            int: The number of days between the two notes.
        """
        return (self.date - other.date).days

    def __repr__(self) -> str:
        """
        Returns a string representation of the NoteSection.

        Returns:
            str: String representation of the NoteSection.
        """
        chars = f'len: {len(self.content)} chars'
        author = f'author={self.author}'
        dt = f'date={self.date.strftime("%Y-%m-%d")}, time={self.time}'
        return f"NoteSection(type={self.type}, {dt}, {author}, {chars})"

    def to_markdown(self) -> str:
        """
        Returns the note section as a markdown string.

        Returns:
            str: The note section in markdown format.
        """
        return f"# {self.type}, {self.date.strftime('%Y-%m-%d')}, {self.time}, {self.author}\n\n{self.content}"

    @property
    def is_progress_note(self) -> bool:
        """
        True if the note type is a progress note, False otherwise.
        """
        if self.language == "original":
            return self.type.startswith('Progress')
        else:
            raise ValueError(f"Unsupported language: {self.language}")
