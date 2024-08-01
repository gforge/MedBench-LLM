from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.retrievers import RunnableSerializable
from langchain_core.language_models import BaseChatModel

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


# Generate the hospital course
def generate_hospital_course(
    day1: str,
    progress: str,
    operation: str,
    progress_lab: str,
    llm: BaseChatModel,
):

    output_parser = StrOutputParser()

    ED_extract_template = ChatPromptTemplate.from_template(prompt_ED_extract)

    output_parser_json = JsonOutputFunctionsParser()

    ed_extract_chain = ED_extract_template | llm.bind(
        function_call={"name": "Extraction_hosp_course"},
        functions=extracted_functions_hosp_course) | output_parser_json

    ED_generate_template = ChatPromptTemplate.from_template(prompt_ED_generate)

    ED_extract_generate_chain = ({
        "Extracted_ED_Notes": ed_extract_chain
    }
                                 | ED_generate_template
                                 | llm
                                 | StrOutputParser())

    progress_sum_template = ChatPromptTemplate.from_template(
        prompt_progress_sum)

    progress_sum_chain = progress_sum_template | llm | output_parser

    lab_trend_template = ChatPromptTemplate.from_template(prompt_lab_trend)

    lab_trend_chain = lab_trend_template | llm | output_parser

    op_sum_template = ChatPromptTemplate.from_template(prompt_op_sum)

    op_sum_chain = op_sum_template | llm | output_parser

    combine_template = ChatPromptTemplate.from_template(prompt_combine)

    ED_extract_generate_chain: RunnableSerializable[dict, str] = (
        {
            "initial_hosp_course": ED_extract_generate_chain,
            "progress_sum": progress_sum_chain,
            "lab_trends": lab_trend_chain,
            "op_sum": op_sum_chain
        }
        | combine_template
        | llm
        | StrOutputParser())

    args = {
        "ED_Notes": day1,
        "Progress_Notes": progress,
        "Progress_Lab_Notes": progress_lab,
        "Op_Notes": operation
    }
    discharge_hosp_course = ED_extract_generate_chain.invoke(args)

    return discharge_hosp_course
