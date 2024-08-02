from datetime import date
from typing import Union

from pydantic import BaseModel, Field


class Medication(BaseModel):
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

    def toString(self):
        return f"{self.medication} {self.strength} {self.unit} ({self.way_of_administration}) {self.times_per_day}"

    def __str__(self) -> str:
        return self.toString()


class LabTest(BaseModel):
    lab_test: str = Field(..., alias='labTest')
    reference_interval: str = Field(..., alias='referenceInterval')
    unit: str
    value: Union[str, int, float]  # Can accept string, int, or float
    date: date
    time: str

    def toString(self):
        return f"{self.lab_test} {self.value} {self.unit} ({self.reference_interval})"

    def __str__(self) -> str:
        return self.toString()


class Case(BaseModel):
    id: str
    language: str
    lab: str
    singleLab: list[LabTest]
    medications: str
    singleMedication: list[Medication]
    chart: str

    def __rep__(self):
        labs = f'{len(self.singleLab)} labs'
        meds = f'{len(self.singleMedication)} medications'
        notes = f'{len(self.chart)} characters of notes'

        return f"Case({self.id} [{self.language}], {labs}, {meds}, {notes})"
