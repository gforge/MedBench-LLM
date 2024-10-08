# Function to generate section 1
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from helpers import Case

from .read_decompose_prompt import read_decompose_prompt as read


def generate_operation_section(case: Case, llm: BaseChatModel):
    """
    Generates operation section of the discharge summary based on the provided operation notes.

    Args:
        case (Case): The case object containing surgery notes
        llm (BaseChatModel): The language model used for generating the discharge summary.

    Returns:
        str: The operation section of the discharge summary.
    """
    output_parser = StrOutputParser()

    op_details_extract_template = ChatPromptTemplate.from_template(
        read(
            'op_details_extact',
            language=case.language,
            prefix_system_prompt=True,
        ))

    op_details_extract_chain = op_details_extract_template | llm | output_parser

    op_details = op_details_extract_chain.invoke({"note": case.surgery})

    return op_details
