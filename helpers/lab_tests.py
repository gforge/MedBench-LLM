from datetime import date
from typing import Literal, Union

from pydantic import BaseModel, Field


class LabTest(BaseModel):
    """
    Holds the information of a single lab test
    """
    lab_test: str = Field(..., alias='labTest')
    reference_interval: str = Field(..., alias='referenceInterval')
    unit: str
    value: Union[str, int, float]  # Can accept string, int, or float
    date: date
    time: str

    def to_string(self):
        """
        Returns a string representation of the lab test as it would
        be represented in a report
        """
        return f"{self.lab_test} {self.value} {self.unit} ({self.reference_interval})"

    def __str__(self) -> str:
        return self.to_string()
