import pandas as pd
from langchain_core.language_models import BaseChatModel

from helpers import Case

from .generate_discharge_meds import generate_discharge_meds
from .generate_hospital_course import generate_hospital_course
from .generate_operation_section import generate_operation_section
from .generate_plan import generate_plan
from .generate_section_1 import generate_section_1


def single_section(case: Case, llm: BaseChatModel) -> str:
    """
    Combines different sections of a medical case into a single string.

    Args:
        case (CaseWithSubsections): The medical case with subsections.
        llm (BaseChatModel): The language model used for generating text.

    Returns:
        str: The combined sections as a single string.
    """
    section_1_notes = generate_section_1(
        day1=case.first_day,
        progress=case.progress,
        llm=llm,
    )

    operation_note_section = generate_operation_section(operation=case.surgery,
                                                        llm=llm)

    hospital_course_section = generate_hospital_course(
        day1=case.first_day,
        progress=case.progress,
        operation=case.surgery,
        progress_lab=case.progress,
        llm=llm,
    )
    plan_section = generate_plan(
        plan=case.last_surgery_and_progress_notes,
        llm=llm,
    )
    medication_section = generate_discharge_meds(
        meds=case.medications,
        llm=llm,
    )

    return "\n\n".join([
        section_1_notes, operation_note_section, hospital_course_section,
        plan_section, medication_section
    ])


def combine_all_sections(case: Case, llm: BaseChatModel, n: int):
    """
    Combines the outputs of multiple calls to the `single_section` function
    into a single DataFrame.

    Args:
        case (Case): The case object containing subsections.
        llm (BaseChatModel): The language model used for generating outputs.
        n (int): The number of times to call the `single_section` function.

    Returns:
        pd.DataFrame: A DataFrame containing the combined outputs of the
        `single_section` function.
    """
    decompose_list_outputs = []

    for _ in range(n):
        single_output = single_section(case, llm)

        decompose_list_outputs.append(single_output)

    df_decompose = pd.DataFrame([list(decompose_list_outputs)])
    df_decompose.index = ["decompose_sum"]

    return df_decompose
