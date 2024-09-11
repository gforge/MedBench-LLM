from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.runnables import RunnableSerializable
from helpers.read_prompt import read_dual_prompt, read_single_prompt

current_file_folder = Path(__file__).parent / 'prompts'


@dataclass
class TypesOutput:
    """
    Represents the output types.

    Attributes:
        single (str): The single output type.
        dual (str): The dual output type.
    """
    single: str
    dual: str


def get_dual_prompt(llm: BaseChatModel, language: str) -> RunnableSerializable:
    """
    Get the dual prompt template.

    Args:
    - llm: The language model.
    - language (str): The language of the prompt.

    Returns:
    - ChatPromptTemplate: The dual prompt
    """

    basic_dual_prompt = read_dual_prompt('basic',
                                         prompt_path=current_file_folder,
                                         language=language)
    return (ChatPromptTemplate.from_messages(
        [
            ("system", basic_dual_prompt.system),
            ("human", basic_dual_prompt.human),
        ],
        template_format="f-string",
    )
            | llm
            | StrOutputParser())


def create_multiple_type_outputs(
    case: str,
    language: str,
    n: int,
    llm: BaseChatModel,
) -> list[TypesOutput]:
    """
    Create a list of TypesOutput based on the provided chains and case.

    Args:
    - chains: ChainTypes object containing both and human runnables.
    - case: Dictionary representing the entire clinical charts (e.g., progress, op, medication, lab).
    - n: Number of iterations to invoke chains.

    Returns:
    - List of TypesOutput objects with results from both system and human chains.
    """
    args = {"notes": case}

    dual = get_dual_prompt(llm=llm, language=language)
    single = (ChatPromptTemplate.from_messages(
        [
            ("human",
             read_single_prompt(
                 'basic_both',
                 prompt_path=current_file_folder,
                 language=language,
             )),
        ],
        template_format="f-string",
    )
              | llm
              | StrOutputParser())

    def run_chain() -> TypesOutput:
        try:
            single_output = single.invoke(args)
            dual_output = dual.invoke(args)
        except Exception as e:
            print(f"Error invoking chain: {e}")
            single_output, dual_output = "Error", "Error"
        return TypesOutput(single=single_output, dual=dual_output)

    ret = [run_chain() for _ in range(n)]

    return ret


def convert_to_df(outputs: list[TypesOutput]) -> pd.DataFrame:
    """
    Convert a list of TypesOutput into a pandas DataFrame.

    Args:
    - outputs: List of TypesOutput objects.

    Returns:
    - DataFrame with columns 'both' and 'human'.
    """
    return pd.DataFrame([asdict(output) for output in outputs])


def create_multiple_basic_prompts(
    case: str,
    language: str,
    n: int,
    llm: BaseChatModel,
) -> pd.DataFrame:
    """
    Create a DataFrame with the results of invoking both system and human chains.

    Args:
    - chains: ChainTypes object containing both and human runnables.
    - case: Dictionary representing the entire clinical charts (e.g., progress, op, medication, lab).
    - n: Number of iterations to invoke chains.

    Returns:
    - DataFrame with columns 'both' and 'human'.
    """
    outputs = create_multiple_type_outputs(case=case,
                                           language=language,
                                           n=n,
                                           llm=llm)
    return convert_to_df(outputs)
