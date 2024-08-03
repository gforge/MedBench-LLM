from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import RunnableSerializable

from helpers import Case
from .read_decompose_prompt import read_decompose_prompt

# Plan
# Instructions on when follow up-visits are planned. Found in the progress notes.
# If the patient has received sutures these should be removed 2-3 weeks after the last surgery.
# Information on when to contact the orthopaedic outpatient clinic or the emergency department.
#   For example; signs of infection such as redness, swollenness, fever etc.
# Level of mobilization: Full weight-bearing? Partial weight bearing? No weight bearing? Can
#   usually be found in the last operative note. If nothing is stated usually full mobilization is allowed.

# Extract out the relevant information and put it in a structure output
extracted_functions_plan = [{
    "name": "Extraction_Plan",
    "description": "All extracted information from the documents",
    "parameters": {
        "type": "object",
        "properties": {
            "Instructions": {
                "type":
                "string",
                "description":
                "instructions related to follow-up visits, management of conditions, precautions"
            },
            "Level of mobilization": {
                "type": "string",
                "description": "weight bearing ability of the patient"
            },
            "suture present": {
                "type":
                "string",
                "description":
                "a boolean variable, true if suture is present and false if no suture"
            },
        }
    }
}]

prompt_plan_generate = read_decompose_prompt('plan_generate')
prompt_plan_extract = read_decompose_prompt('plan_extract')


def generate_plan(case: Case, llm: BaseChatModel):
    """
    Generates a discharge plan based on the given plan and language model.

    Args:
        plan (str): The plan to generate a discharge plan from.
        llm (BaseChatModel): The language model used for generating the discharge plan.

    Returns:
        str: The generated discharge plan.
    """

    plan_extract_template = ChatPromptTemplate.from_template(
        prompt_plan_extract)

    output_parser_json = JsonOutputFunctionsParser()

    plan_extract_chain = plan_extract_template | llm.bind(
        function_call={"name": "Extraction_Plan"},
        functions=extracted_functions_plan) | output_parser_json

    plan_generate_template = ChatPromptTemplate.from_template(
        prompt_plan_generate)

    plan_extract_generate_chain: RunnableSerializable[dict, str] = (
        {
            "Extracted_Plan_Notes": plan_extract_chain
        }
        | plan_generate_template
        | llm
        | StrOutputParser())

    discharge_plan = plan_extract_generate_chain.invoke(
        {"Plan_Notes": case.last_surgery_and_progress_notes})

    return discharge_plan
