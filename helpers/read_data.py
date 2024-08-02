import json
from pathlib import Path

from .case import Case


def read_markdown_file(path: Path) -> str:
    """
    Read the contents of a markdown file.

    Args:
        path (Path): The path to the markdown file.

    Returns:
        str: The contents of the markdown file.

    Raises:
        FileNotFoundError: If the file specified by the path does not exist.
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError as e:
        msg = f'File not found for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e


def read_json_file(path: Path) -> Case:
    """
    Reads a JSON file and returns a Case object.

    Args:
        path (Path): The path to the JSON file.

    Returns:
        Case: The Case object created from the JSON data.

    Raises:
        FileNotFoundError: If the file is not found at the specified path.
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Convert filename "markdown_Cardiology_Case 1_original.json"
            # to id = "Cardiology_Case 1"
            # language = "original"
            core_name = path.stem.replace('markdown_', '')
            # Check that file name is in the correct format
            if len(core_name.split('_')) < 3:
                raise ValueError(
                    f"File name '{core_name}' is not in the correct format")
            data['language'] = core_name.split('_')[-1]
            data['id'] = '_'.join(core_name.split('_')[:-1])

            return Case(**data)

    except FileNotFoundError as e:
        msg = f'File not found for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e
