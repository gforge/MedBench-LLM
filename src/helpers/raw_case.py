from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .lab_tests import LabTest
from .medications import Medication
from .single_day import SingleDay
from .types import Language, Style, parse_language_input


class RawCase(BaseModel):
    """
    Holds the information of a single case
    """

    id: str

    language: Language
    """
    The language of the case (English, Swedish, etc.)
    """

    style: Style = "plain"
    """
    The style of the case content:
    - plain: No abbreviations, uses SNOMED terms, universally understandable
    - clinical: Hospital-style with locale-specific abbreviations
    """

    specialty: Literal["Orthopaedics", "Medicine"]
    """
    The specialty of the case. Currently only 'Orthopaedics' is supported.
    Each language will require it's own prompts.
    """

    lab: str
    singleLab: list[LabTest]
    medications: str
    singleMedication: list[Medication]
    chart: str

    daily_data: list[SingleDay] = Field(default_factory=list)

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        """
        Normalize language input to a valid Language value.
        Handles 'original' -> 'English' and capitalization.
        """
        lang, _ = parse_language_input(value)
        return lang

    @field_validator("style", mode="before")
    @classmethod
    def normalize_style(cls, value: str | None, info) -> str:
        """
        Extract style from language input if provided as compound format.
        """
        if value is not None:
            return value

        # Try to extract from language field if it's compound
        lang_input = info.data.get("language", "")
        if isinstance(lang_input, str):
            _, style = parse_language_input(lang_input)
            return style
        return "plain"

    class Config:
        """
        Pydantic configuration
        """

        arbitrary_types_allowed = True
