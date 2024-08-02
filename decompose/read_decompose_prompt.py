from pathlib import Path

from helpers.read_prompt import read_single_prompt

current_parent_folder = Path(__file__).parent / 'prompts'


def read_decompose_prompt(prompt_name: str):
    """
    Reads and decomposes a prompt from a specific prompt file.

    Args:
        prompt_name (str): The name of the prompt to read.

    Returns:
        str: The decomposed prompt.

    """
    return read_single_prompt(prompt_name, prompt_path=current_parent_folder)
