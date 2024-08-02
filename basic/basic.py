from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import RunnableSerializable

from helpers.read_prompt import read_dual_prompt, read_single_prompt

current_file_folder = Path(__file__).parent / 'prompts'
basic_dual_prompt = read_dual_prompt(
    'basic',
    prompt_path=current_file_folder,
)
single_basic_prompt = read_single_prompt(
    'basic_both',
    prompt_path=current_file_folder,
)


@dataclass
class ChainTypes:
    """
    ChainTypes class represents the types of chains in the MedBench LLM basic module.

    Attributes:
        dual (RunnableSerializable[dict, str]): Represents a dual chain.
        single (RunnableSerializable[dict, str]): Represents a single chain.
    """
    dual: RunnableSerializable[dict, str]
    single: RunnableSerializable[dict, str]


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


def create_multiple_type_outputs(
    case: str,
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
    chains = basic_chain(llm=llm)

    def run_chain() -> TypesOutput:
        try:
            single_output = chains.single.invoke(args)
            dual_output = chains.dual.invoke(args)
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
    outputs = create_multiple_type_outputs(case=case, n=n, llm=llm)
    return convert_to_df(outputs)


def basic_chain(llm: BaseChatModel) -> ChainTypes:
    """
    Executes a basic chain of prompts using the given language model.

    Args:
        llm (BaseChatModel): The language model used for generating responses.

    Returns:
        ChainTypes: An object containing the dual and single chains of prompts.
    """

    output_parser = StrOutputParser()

    return ChainTypes(
        dual=(ChatPromptTemplate.from_messages([
            ("system", basic_dual_prompt.system),
            ("human", basic_dual_prompt.human),
        ],
                                               template_format="f-string")
              | llm
              | output_parser),
        single=(ChatPromptTemplate.from_messages([
            ("human", single_basic_prompt),
        ],
                                                 template_format="f-string")
                | llm
                | output_parser))
