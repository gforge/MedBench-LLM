from dataclasses import asdict, dataclass

import pandas as pd
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import RunnableSerializable

from .read_prompt import read_dual_prompt, read_single_prompt


@dataclass
class ChainTypes:
    dual: RunnableSerializable[dict, str]
    single: RunnableSerializable[dict, str]


@dataclass
class TypesOutput:
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


basic_dual_prompt = read_dual_prompt('basic')
single_basic_prompt = read_single_prompt('basic_both')


def basic_chain(llm: BaseChatModel) -> ChainTypes:
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
