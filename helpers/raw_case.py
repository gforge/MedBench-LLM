from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .lab_tests import LabTest
from .medications import Medication
from .single_day import SingleDay


class RawCase(BaseModel):
    """
    Holds the information of a single case
    """
    id: str

    language: Literal['English', "Swedish"]
    """
    The language of the case. Currently only 'original' is supported
    that is equal to simple English. Each language will require it's own prompts.
    The language is also capitalized and original as input will
    be converted to 'English'.
    """

    specialty: Literal['Orthopaedics']
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

    @field_validator('language', mode='before')
    @classmethod
    def convert_and_capitalize_language(cls, value: str) -> str:
        """
        Converts 'original' to 'English' and capitalizes other language values.
        """
        if value.lower() == 'original':
            return 'English'
        return value.capitalize()

    class Config:
        """
        Pydantic configuration
        """
        arbitrary_types_allowed = True
