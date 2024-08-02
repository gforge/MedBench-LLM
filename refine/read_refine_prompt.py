from pathlib import Path

from helpers.read_prompt import read_single_prompt

current_parent_folder = Path(__file__).parent / 'prompts'


def read_refine_prompt(prompt_name):
    """
    Reads and decomposes a prompt from a specific prompt file.
    """
    return read_single_prompt(prompt_name, prompt_path=current_parent_folder)
