from langchain.docstore.document import Document

from prompting.CaseWithSubsections import CaseWithSubsections


def load_docs(case: CaseWithSubsections) -> list[Document]:
    """
    Load documents for each day of a given case.

    Args:
        case (CaseWithSubsections): The case object containing the days and content.

    Returns:
        list[Document]: A list of Document objects, each representing a day's content.
    """
    list_of_docs = []

    for i in range(case.days):
        doc = Document(page_content=case.get_day(i + 1))
        list_of_docs.append(doc)

    return list_of_docs
