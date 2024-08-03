import pandas as pd
from langchain_core.language_models import BaseChatModel

from helpers.case import Case

from .refine import prompt_refine


def create_refine_df(case: Case, n: int, llm: BaseChatModel):
    """
    Creates a DataFrame containing the sum of refined prompts for a given case.

    Args:
        case (CaseWithSubsections): The case for which prompts need to be refined.
        n (int): The number of times to refine the prompts.
        llm (BaseChatModel): The language model used for refining the prompts.

    Returns:
        pd.DataFrame: A DataFrame containing the summarization of refined prompts.
    """
    refine_sum = [prompt_refine(case=case, llm=llm) for _ in range(n)]
    df_refine = pd.DataFrame([list(refine_sum)])
    df_refine.index = ["refine_sum"]

    return df_refine
