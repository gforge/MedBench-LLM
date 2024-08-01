import pandas as pd
from langchain_core.language_models import BaseChatModel

from prompting import CaseWithSubsections
from .map_reduce import mapreduce


def create_mapreduce_df(case: CaseWithSubsections, n: int, llm: BaseChatModel):
    mapreduce_sum = [mapreduce(case=case, llm=llm) for _ in range(n)]
    df_mapreduce = pd.DataFrame([list(mapreduce_sum)])
    df_mapreduce.index = ["mapreduce_sum"]

    return df_mapreduce
