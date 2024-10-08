from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from helpers import Case

from .read_decompose_prompt import read_decompose_prompt as read

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


def generate_discharge_meds(case: Case, llm: BaseChatModel):
    """
    Generates discharge medications based on the given input medications and a language model.

    Args:
        meds (list): A list of input medications.
        llm (BaseChatModel): The language model used for generating discharge medications.

    Returns:
        dict: A dictionary containing the generated discharge medications.
    """
    # No system prompt required - included in the prompt (pharmacist role)
    meds_extract_template = ChatPromptTemplate.from_template(
        read(
            'meds_extract',
            language=case.language,
            prefix_system_prompt=False,
        ))

    meds_extract_chain = meds_extract_template | llm | StrOutputParser()

    args = {
        "initial_medication_list": case.get_day(0).get_medications_list(),
        "latest_medication_list": case.get_day(-1).get_medications_list(),
    }
    meds_changes = meds_extract_chain.invoke(args)

    return meds_changes
