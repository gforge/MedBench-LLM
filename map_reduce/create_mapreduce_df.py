import pandas as pd
from langchain_core.language_models import BaseChatModel

from helpers.case import Case
from helpers.case_with_subsections import CaseWithSubsections

from .map_reduce import mapreduce


def create_mapreduce_df(case: Case, n: int, llm: BaseChatModel):
    """
    Create a DataFrame containing the mapreduce sum of the provided case.

    Args:
    - case: CaseWithSubsections object containing the case to summarize.
    - n: Number of iterations to invoke mapreduce.
    - llm: The language model to use.

    Returns:
    - df_mapreduce: DataFrame containing the mapreduce sum of the provided case.
    """
    extended_case = CaseWithSubsections(case)

    mapreduce_sum = [mapreduce(case=extended_case, llm=llm) for _ in range(n)]
    df_mapreduce = pd.DataFrame([list(mapreduce_sum)])
    df_mapreduce.index = ["mapreduce_sum"]

    return df_mapreduce
