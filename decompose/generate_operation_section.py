# Function to generate section 1
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from .read_decompose_prompt import read_decompose_prompt

prompt_operation_notes_extract = read_decompose_prompt(
    'operation_details_extact')


def generate_operation_section(operation: str, llm: BaseChatModel):
    """
    Generates operation section of the discharge summary based on the provided operation notes.

    Args:
        operation (str): The operation note to generate operation section.
        llm (BaseChatModel): The language model used for generating the discharge summary.

    Returns:
        str: The operation section of the discharge summary.
    """
    output_parser = StrOutputParser()

    op_details_extract_template = ChatPromptTemplate.from_template(
        prompt_operation_notes_extract)

    op_details_extract_chain = op_details_extract_template | llm | output_parser

    op_details = op_details_extract_chain.invoke({"note": operation})

    return op_details
