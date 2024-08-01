from langchain.chains.summarize import load_summarize_chain
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from prompting import CaseWithSubsections

from .load_docs import load_docs
from .read_mapreduce_prompt import read_map_reduce_prompt

map_prompt = read_map_reduce_prompt('map')
combine_prompt = read_map_reduce_prompt('combine')


def mapreduce(case: CaseWithSubsections, llm: BaseChatModel) -> str:
    # split the documents in terms of the number of days
    docs = load_docs(case=case)

    map_prompt_template = ChatPromptTemplate.from_template(map_prompt)
    combine_prompt_template = ChatPromptTemplate.from_template(combine_prompt)

    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type='map_reduce',
        map_prompt=map_prompt_template,
        combine_prompt=combine_prompt_template,
    )

    summary = summary_chain.invoke({"input_documents": docs})
    summary_output = summary["output_text"]

    return summary_output
