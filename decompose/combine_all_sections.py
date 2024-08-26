import pandas as pd
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from helpers import Case

from .generate_discharge_meds import generate_discharge_meds
from .generate_hospital_course import generate_hospital_course
from .generate_operation_section import generate_operation_section
from .generate_plan import generate_plan
from .generate_section_1 import generate_section_1
from .read_decompose_prompt import read_decompose_prompt

_human_final_summary = read_decompose_prompt("final_summary")
_system_role_and_guidelines = read_decompose_prompt("system_prompt")


def single_decompose(case: Case, llm: BaseChatModel) -> str:
    """
    Combines different sections of a medical case into a single string.

    Args:
        case (CaseWithSubsections): The medical case with subsections.
        llm (BaseChatModel): The language model used for generating text.

    Returns:
        str: The combined sections as a single string.
    """
    section_1_notes = generate_section_1(case=case, llm=llm)
    operation_note_section = generate_operation_section(case=case, llm=llm)
    hospital_course_section = generate_hospital_course(case=case, llm=llm)
    plan_section = generate_plan(case=case, llm=llm)
    medication_section = generate_discharge_meds(case=case, llm=llm)

    everything = "\n\n".join([
        section_1_notes,
        operation_note_section,
        hospital_course_section,
        plan_section,
        medication_section,
    ])

    output_parser = StrOutputParser()
    return (ChatPromptTemplate.from_messages(
        [
            ("system", _system_role_and_guidelines),
            ("human", _human_final_summary),
        ],
        template_format="f-string",
    )
            | llm
            | output_parser).invoke({"preprocessed_information": everything})


def multiple_decompose(case: Case, llm: BaseChatModel, n: int):
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
        single_output = single_decompose(case, llm)

        decompose_list_outputs.append(single_output)

    df_decompose = pd.DataFrame([list(decompose_list_outputs)])
    df_decompose.index = ["decompose_sum"]

    return df_decompose
