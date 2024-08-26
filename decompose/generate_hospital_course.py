from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from helpers.case import Case

from .read_decompose_prompt import read_decompose_prompt as read

# combine progress notes and lab values
# - Trends in lab tests. For example, a sudden rise in CRP (C-reactive protein) or a drop in Hb (haemoglobin)
#   postoperatively. Found in the progress notes and/or separate lab list.

# combine progress notes
# - Comment on how treatment is coming along. Including but not limited to when antibiotics are started, changed to
#   another intravenous type of antibiotic or when they are changed to an oral antibiotic. Found in the progress notes.
# - Any adverse events such as the occurrence of a new disease and how this is handled. Found in the progress notes.
# - Any discussions with other departments’ consultants. Found in the progress notes.

# operation notes
# - Any operations performed. Found in the progress notes.

# Hospital course: [admission reasons, clinical findings, initiated intervention and treatment]

# Extract the relevant findings from the notes in a structured output
_extracted_functions_hosp_course = [{
    "name": "Extraction_hosp_course",
    "description": "All extracted information from the documents",
    "parameters": {
        "type": "object",
        "properties": {
            "admission reasons": {
                "type": "string",
                "description": "the reasons for current admission"
            },
            "clinical findings": {
                "type": "string",
                "description":
                "any significant clinical findings on examination"
            },
            "intervention and treatment": {
                "type":
                "string",
                "description":
                "all intervention and treatment initiated during admission"
            },
        }
    }
}]

_system_prompt = read('system_prompt')
_prompt_d1_sum = _system_prompt + "\n\n" + read('hosp_d1_sum')
_prompt_progress_sum = _system_prompt + "\n\n" + read('hosp_progress_sum')
_prompt_combine = _system_prompt + "\n\n" + read('hosp_combine')


def generate_hospital_course(
    case: Case,
    llm: BaseChatModel,
) -> str:
    """
    Generates a hospital course based on the provided inputs.

    Args:
        case (Case): The case object containing subsections.
        llm (BaseChatModel): The chat model used for generating the hospital course.

    Returns:
        str: The generated hospital course.

    Raises:
        None
    """

    d1_extract_template = ChatPromptTemplate.from_template(_prompt_d1_sum)

    d1_extract_chain = d1_extract_template | llm | StrOutputParser()

    progress_sum_template = ChatPromptTemplate.from_template(
        _prompt_progress_sum)

    progress_sum_chain = progress_sum_template | llm | StrOutputParser()

    combine_template = ChatPromptTemplate.from_template(_prompt_combine)

    hospital_course_generator = ({
        "day1_summary": d1_extract_chain,
        "progress_summary": progress_sum_chain
    }
                                 | combine_template
                                 | llm
                                 | StrOutputParser())
    # Arguments for invoking the final chain
    args = {
        "d1_note": case.first_day_notes,
        "progress_note": case.get_progress_notes_and_lab(),
    }

    discharge_hosp_course = hospital_course_generator.invoke(args)

    return discharge_hosp_course
