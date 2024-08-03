from langchain.docstore.document import Document

from helpers.case import Case


def load_docs(case: Case) -> list[Document]:
    """
    Load documents for each day of a given case.

    Args:
        case (CaseWithSubsections): The case object containing the days and content.

    Returns:
        list[Document]: A list of Document objects, each representing a day's content.
    """
    list_of_docs = []

    for d in case.daily_data:
        doc = Document(page_content=d.to_markdown())
        list_of_docs.append(doc)

    return list_of_docs
