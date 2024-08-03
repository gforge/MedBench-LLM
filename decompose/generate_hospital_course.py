from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from helpers.case import Case

from .read_decompose_prompt import read_decompose_prompt

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
extracted_functions_hosp_course = [{
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

prompt_ED_extract = read_decompose_prompt('ED_extract')
prompt_ED_generate = read_decompose_prompt('ED_generate')
prompt_progress_sum = read_decompose_prompt('progress_sum')
prompt_lab_trend = read_decompose_prompt('lab_trend')
prompt_op_sum = read_decompose_prompt('op_sum')
prompt_combine = read_decompose_prompt('combine')


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

    output_parser = StrOutputParser()
    output_parser_json = JsonOutputFunctionsParser()

    # Chain for extracting ED notes
    ed_extract_chain = (ChatPromptTemplate.from_template(prompt_ED_extract)
                        | llm.bind(
                            function_call={"name": "Extraction_hosp_course"},
                            functions=extracted_functions_hosp_course)
                        | output_parser_json)

    # Chain for generating ED notes
    ed_generate_chain = ({
        "Extracted_ED_Notes": ed_extract_chain
    }
                         | ChatPromptTemplate.from_template(prompt_ED_generate)
                         | llm
                         | output_parser)

    # Chains for progress summary, lab trends, and operation summary
    progress_sum_chain = (ChatPromptTemplate.from_template(prompt_progress_sum)
                          | llm
                          | output_parser)

    lab_trend_chain = (ChatPromptTemplate.from_template(prompt_lab_trend)
                       | llm
                       | output_parser)

    op_sum_chain = (ChatPromptTemplate.from_template(prompt_op_sum)
                    | llm
                    | output_parser)

    # Combine all the parts into the final hospital course
    final_hospital_course_chain = (
        {
            "initial_hosp_course": ed_generate_chain,
            "progress_sum": progress_sum_chain,
            "lab_trends": lab_trend_chain,
            "op_sum": op_sum_chain
        }
        | ChatPromptTemplate.from_template(prompt_combine)
        | llm
        | output_parser)

    # Arguments for invoking the final chain
    args = {
        "ED_Notes": case.first_day_notes,
        "Progress_Notes": case.progress_notes,
        "Progress_Lab_Notes": case.get_progress_notes_and_lab(),
        "Op_Notes": case.surgery,
    }

    discharge_hosp_course = final_hospital_course_chain.invoke(args)

    return discharge_hosp_course
