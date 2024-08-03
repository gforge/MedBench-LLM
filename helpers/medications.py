from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field


class Medication(BaseModel):
    """
    Holds the information of a single medication
    """
    medication: str = Field(
        ..., example="Losartad Comp (Losartan/Hydrochlortiazide)")
    way_of_administration: str = Field(...,
                                       example="PO",
                                       alias='wayOfAdministration')
    strength: Union[str, int, float] = Field(..., example="50/12,5")
    unit: str = Field(..., example="mg")
    times_per_day: Union[str, int, float,
                         None] = Field(...,
                                       example="1+0+0",
                                       alias='timesPerDay')

    date: date

    def to_string(self):
        """
        Returns a string representation of the medication as it would
        be represented in a report
        """
        return f"{self.medication} {self.strength} {self.unit} ({self.way_of_administration}) {self.times_per_day}"

    def __str__(self) -> str:
        return self.to_string()
