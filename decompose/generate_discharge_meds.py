from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import RunnableSerializable

from .read_decompose_prompt import read_decompose_prompt

# Discharge Medications
# Medications used during the patient’s hospital stay. Found in separate list of medications.
# Any previously prescribed medications. Changes should be noted. Found in the progress notes.
# Any newly prescribed medications including dose, number of pills per day and for how long these should be taken.
#   Information can be found in the progress notes and/or the separate list of medications.

# Extract out relevant medication related information and put it in a structured output
extracted_medication = [{
    "name": "Extraction_Meds",
    "description": "All extracted information from the documents",
    "parameters": {
        "type": "object",
        "properties": {
            "medication used": {
                "type": "string",
                "description":
                "all medication used during patient's hospital stay"
            },
            "medication changes": {
                "type":
                "string",
                "description":
                "any changes to the medication when the patient is first admitted "
            },
            "newly prescribed medication": {
                "type": "string",
                "description": "any new medication prescribed on the last day"
            },
        }
    }
}]

prompt_meds_extract = read_decompose_prompt('meds_extract')
prompt_meds_generate = read_decompose_prompt('meds_generate')


def generate_discharge_meds(meds, llm: BaseChatModel):
    """
    Generates discharge medications based on the given input medications and a language model.

    Args:
        meds (list): A list of input medications.
        llm (BaseChatModel): The language model used for generating discharge medications.

    Returns:
        dict: A dictionary containing the generated discharge medications.
    """
    meds_extract_template = ChatPromptTemplate.from_template(
        prompt_meds_extract)

    output_parser_json = JsonOutputFunctionsParser()

    meds_extract_chain = (meds_extract_template
                          | llm.bind(function_call={"name": "Extraction_Meds"},
                                     functions=extracted_medication)
                          | output_parser_json)

    meds_generate_template = ChatPromptTemplate.from_template(
        prompt_meds_generate)

    meds_extract_generate_chain: RunnableSerializable[dict, str] = (
        {
            "Extracted_medication_details": meds_extract_chain
        }
        | meds_generate_template
        | llm
        | StrOutputParser())

    discharge_meds = meds_extract_generate_chain.invoke(
        {"Medication_details": meds})

    return discharge_meds
