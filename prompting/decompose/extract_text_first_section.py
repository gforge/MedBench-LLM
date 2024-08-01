from langchain_core.runnables import RunnableLambda


def extract_text_first_section(text: str) -> str:
    """
    Extracts the first section of text from the given input text.

    Args:
      text (str): The input text.

    Returns:
      str: The extracted first section of text.
    """
    main_diagnosis_onwards = text.split("Main Diagnosis:")[1]
    main_diagnosis_string = "Main Diagnosis:" + main_diagnosis_onwards

    split_list = [
        el for el in main_diagnosis_string.split("\n") if len(el.strip()) > 0
    ]

    until_reason = split_list[:6]

    joined_string = "\n\n".join(until_reason)

    return joined_string


extract_first_section_only = RunnableLambda(extract_text_first_section)
