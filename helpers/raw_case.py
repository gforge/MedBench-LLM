from typing import Literal

from pydantic import BaseModel, Field

from .lab_tests import LabTest
from .medications import Medication
from .single_day import SingleDay


class RawCase(BaseModel):
    """
    Holds the information of a single case
    """
    id: str

    language: Literal['original']
    """
    The language of the case. Currently only 'original' is supported
    that is equal to simple English.
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

    class Config:
        """
        Pydantic configuration
        """
        arbitrary_types_allowed = True
