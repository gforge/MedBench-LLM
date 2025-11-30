from datetime import date
from typing import Union

from pydantic import BaseModel, Field


class Medication(BaseModel):
    """
    Holds the information of a single medication
    """

    medication: str = Field(description="Medication name")
    way_of_administration: str = Field(alias="wayOfAdministration", description="Route of administration")
    strength: Union[str, int, float] = Field(description="Medication strength")
    unit: str = Field(description="Unit of measurement")
    times_per_day: Union[str, int, float, None] = Field(alias="timesPerDay", description="Dosage schedule")

    date: date

    def to_string(self) -> str:
        """
        Returns a string representation of the medication as it would
        be represented in a report
        """
        return f"{self.medication} {self.strength} {self.unit} ({self.way_of_administration}) {self.times_per_day}"

    def __str__(self) -> str:
        return self.to_string()
