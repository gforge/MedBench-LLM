from langchain.chains.summarize import load_summarize_chain
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from helpers.case_with_subsections import CaseWithSubsections
from map_reduce.load_docs import load_docs

from .read_refine_prompt import read_refine_prompt

generate_refine_prompt = read_refine_prompt('generate')
refine_template_clindoc = read_refine_prompt('clindoc')
generate_refine_sum_prompt = read_refine_prompt('summarize')


def prompt_refine(case: CaseWithSubsections, llm: BaseChatModel):

    docs = load_docs(case)

    output_parser = StrOutputParser()

    prompt_refine_clindoc = ChatPromptTemplate.from_template(
        generate_refine_prompt)

    refine_prompt_clindoc = ChatPromptTemplate.from_template(
        refine_template_clindoc)

    chain = load_summarize_chain(
        llm=llm,
        chain_type="refine",
        question_prompt=prompt_refine_clindoc,
        refine_prompt=refine_prompt_clindoc,
        return_intermediate_steps=True,
        input_key="input_documents",
        output_key="output_text",
    )

    result_clindoc = chain.invoke({"input_documents": docs},
                                  return_only_outputs=True)

    conversation_sum = result_clindoc["output_text"]

    clinc_sum_prompt = ChatPromptTemplate.from_template(
        generate_refine_sum_prompt)

    generate_refine_chain = clinc_sum_prompt | llm | output_parser

    refine_sum = generate_refine_chain.invoke({"text": conversation_sum})

    return refine_sum
