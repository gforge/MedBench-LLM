import json
from pathlib import Path

from .case import Case
import re


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


languages_available = ['original']


def read_json_file(path: Path) -> Case:
    """
    Reads a JSON file and returns a Case object.

    Args:
        path (Path): The path to the JSON file.

    Returns:
        Case: The Case object created from the JSON data.

    Raises:
        FileNotFoundError: If the file is not found at the specified path.
        ValueError: If the file is not a JSON file or if the file name is not in the correct format.
    """
    try:
        if (path.suffix != '.json'):
            raise ValueError(f"File '{path}' is not a JSON file.",
                             "Please provide a JSON file.")

        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Convert filename "markdown_Cardiology_Case 1_original.json"
            # to id = "Cardiology_Case 1"
            # language = "original"
            pattern = re.compile(
                f'^markdown_([^_]+)_(.+)_({"|".join(languages_available)})$')
            match = pattern.match(path.stem)
            if not match:
                raise ValueError(
                    f"File name '{path.stem}' is not in the correct format.",
                    "Expected format: markdown_specialty_id_language.json")
            data['specialty'] = match.group(1)
            data['id'] = match.group(2)
            data['language'] = match.group(3)

            return Case(**data)

    except FileNotFoundError as e:
        msg = f'File not found for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e
