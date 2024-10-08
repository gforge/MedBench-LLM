# Function to generate section 1
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from helpers import Case

from .read_decompose_prompt import read_decompose_prompt as read


def generate_section_1(case: Case, llm: BaseChatModel):
    """
    Generates section 1 of the discharge summary based on the day 1 note and progress note.

    Args:
        case (Case): The case object containing day 1 notes and progress notes.
        llm (BaseChatModel): The language model used for generating the discharge summary.

    Returns:
        str: The generated section 1 of the discharge summary.
    """
    ed_extract_template = ChatPromptTemplate.from_template(
        read(
            's1_ED_extract',
            language=case.language,
            prefix_system_prompt=True,
        ))
    output_parser = StrOutputParser()

    ed_extract_chain = ed_extract_template | llm | output_parser

    progress_sec_diagnosis_prompt = ChatPromptTemplate.from_template(
        read(
            's1_sec_diagnosis_extract',
            language=case.language,
            prefix_system_prompt=True,
        ))

    progress_sec_diagnosis_chain = progress_sec_diagnosis_prompt | llm | output_parser

    section_1_sum_prompt = ChatPromptTemplate.from_template(
        read(
            's1_generate',
            language=case.language,
            prefix_system_prompt=True,
        ))

    section_1_summary_chain = (
        {
            "previous_information": ed_extract_chain,
            "updated_secondary_diagnosis_list": progress_sec_diagnosis_chain
        }
        | section_1_sum_prompt
        | llm
        | output_parser)

    args = {"note": case.first_day_notes, "progress_note": case.progress_notes}
    discharge_sum_1 = section_1_summary_chain.invoke(args)

    return discharge_sum_1
