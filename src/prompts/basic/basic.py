from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable

from helpers.case import Case
from helpers.read_prompt import read_dual_prompt
from helpers.summarize_result import SummarizeResult

current_file_folder = Path(__file__).parent / "prompts"


def get_dual_prompt(llm: BaseChatModel, language: str) -> RunnableSerializable:
    """Get the dual prompt template chain.

    Args:
        llm: The language model instance.
        language: The language of the prompt (e.g., "English", "Swedish").

    Returns:
        A runnable chain that generates summaries from clinical notes.
    """
    basic_dual_prompt = read_dual_prompt("basic", prompt_path=current_file_folder, language=language)
    return (
        ChatPromptTemplate.from_messages(
            [
                ("system", basic_dual_prompt.system),
                ("human", basic_dual_prompt.human),
            ],
            template_format="f-string",
        )
        | llm
        | StrOutputParser()
    )


def summarize(llm: BaseChatModel, language: str, case: Case) -> SummarizeResult:
    """Generate a summary from clinical notes using the basic approach.

    Args:
        llm: The language model instance.
        language: The language of the prompt and notes.
        case: The Case object containing all clinical data.

    Returns:
        SummarizeResult with the generated summary and metadata.
    """
    chain = get_dual_prompt(llm=llm, language=language)
    summary = chain.invoke({"notes": case.chart})
    return SummarizeResult(
        summary=summary,
        num_api_calls=1,
    )
