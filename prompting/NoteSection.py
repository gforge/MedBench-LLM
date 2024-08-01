from datetime import datetime
import re


class NoteSection():
    """
    Represents a note section with type, date, time, author, content, and raw data.

    Attributes:
        type (str): The type of the note.
        date (str): The date of the note in the format 'YYYY-MM-DD'.
        time (str): The time of the note in the format 'HH:MM'.
        author (str): The author of the note.
        content (str): The content of the note.
        raw (str): The raw data of the note.

    Methods:
        __init__(raw: str): Initializes a new instance of the NoteSection class.

    """

    type: str
    date: datetime
    time: str  # 12:00 format
    author: str
    content: str
    raw: str

    def __init__(self, raw: str) -> None:
        """
        Initializes a new instance of the NoteSection class.

        Args:
            raw (str): The raw data of the note.

        Raises:
            AssertionError: If the first line does not have 4 elements, if the note type is empty,
                if the date is not in the format 'YYYY-MM-DD', if the time is not in the format 'HH:MM',
                or if the author is empty.

        """
        lines = raw.strip().split("\n")
        # Get the first line to get the type, date, time, and author
        elements = lines[0].split(", ")
        assert len(
            elements
        ) == 4, f"The first line should have 4 elements, but got {len(elements)} from '{lines[0]}'" + \
            ", entire note: '{raw}'"
        noteType, date, time, author = [e.strip() for e in elements]
        content = "\n".join(lines[1:])

        assert len(noteType) > 0, "Note type should not be empty"
        assert len(date) == 10, "Date should be in YYYY-MM-DD format"
        assert re.match(r"\d{4}-\d{2}-\d{2}",
                        date), "Date should be in YYYY-MM-DD format"
        assert len(time) == 5, "Time should be in HH:MM format"
        assert len(author) > 0, "Author should not be empty"

        self.type = noteType.replace("# ", "").strip()
        # Convert date str to datetime object
        # Assert that date is in the 2022-01-01 format using regex
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.time = time
        self.author = author
        self.content = content
        self.raw = raw

    def days_between(self, other: 'NoteSection') -> int:
        """
        Returns the number of days between the date of this note and the date of another note.
        If the other note is after this note, the result will be positive.

        Args:
            other (NoteSection): The other note to compare dates with.

        Returns:
            int: The number of days between the two notes.

        """
        return (self.date - other.date).days

    def __repr__(self):
        chars = f'len: {len(self.content)} chars'
        author = f'author={self.author}'
        dt = f'date={self.date}, time={self.time}'
        return f"NoteSection(type={self.type}, {dt}, {author}, {chars})"
