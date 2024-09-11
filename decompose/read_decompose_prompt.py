from pathlib import Path

from helpers.read_prompt import read_single_prompt

current_parent_folder = Path(__file__).parent / 'prompts'


def read_decompose_prompt(
    prompt_name: str,
    language: str,
    prefix_system_prompt: bool,
) -> str:
    """
    Reads and decomposes a prompt from a specific prompt file.

    Args:
        prompt_name (str): The name of the prompt to read.
        language (str): The language of the prompt.
        prefix_system_prompt (bool): Whether to prefix the system prompt (system_prompt)

    Returns:
        str: The decomposed prompt.

    """
    prefix = ''
    if prefix_system_prompt:
        prefix = read_single_prompt("system_prompt",
                                    prompt_path=current_parent_folder,
                                    language=language) + '\n\n'

    return prefix + read_single_prompt(
        prompt_name, prompt_path=current_parent_folder, language=language)
