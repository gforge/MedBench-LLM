from pathlib import Path

from prompting.read_prompt import read_single_prompt


def read_decompose_prompt(prompt_name):
    return read_single_prompt(prompt_name,
                              prompt_path=Path('decompose/prompts'))
