# Function to generate section 1
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.language_models import BaseChatModel

from .extracted_structure import extracted_functions
from .extract_text_first_section import extract_first_section_only
from .read_decompose_prompt import read_decompose_prompt

prompt_first_day_summarise = read_decompose_prompt('first_day_summarise')
prompt_extact_progress_sec_diagnosis = read_decompose_prompt('progress_extract_sec_diagnosis')
prompt_generate_section_1 = read_decompose_prompt('section1_generate')


def generate_section_1(day1: str, progress: str, llm: BaseChatModel):
    """
    Generates section 1 of the discharge summary based on the day 1 note and progress note.

    Args:
        day 1 (str): The day 1 note to generate section 1 from.
        progress (str): The progress note that provide additional secondary diagnosis to be included in section 1.
        llm (BaseChatModel): The language model used for generating the discharge summary.

    Returns:
        str: The generated section 1 of the discharge summary.
    """
    output_parser = StrOutputParser()

    first_day_summarise_template = ChatPromptTemplate.from_template(prompt_first_day_summarise)

    first_day_summarise_chain = first_day_summarise_template | llm | output_parser

    extact_progress_sec_diagnosis_template = ChatPromptTemplate.from_template(prompt_extact_progress_sec_diagnosis)

    progress_sec_diagnosis_chain = extact_progress_sec_diagnosis_template | llm | StrOutputParser()

    section_1_sum_template = ChatPromptTemplate.from_template(prompt_generate_section_1)

    generate_section_1 = ( {"previous_information": first_day_summarise_chain,
                           "updated_secondary_diagnosis_list": progress_sec_diagnosis_chain}
                                     | section_1_sum_template 
                                     | llm
                                     | StrOutputParser()
                                    )

    # Run
    discharge_sum_1 = generate_section_1.invoke({"note": day1, "progress_note": progress})
    
    return discharge_sum_1
