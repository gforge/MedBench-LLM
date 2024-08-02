from dataclasses import dataclass
from pathlib import Path


@dataclass
class DualPrompt:
    """
    Represents a dual prompt with two different prompts.
    """
    system: str
    human: str


def read_single_prompt(name: str, prompt_path: Path) -> str:
    """
    Read a single prompt from the provided path.

    Args:
    - name: Name of the prompt file to read.
    - prompt_path: Path to the prompt directory.
    """
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt directory not found at {prompt_path}")

    base = Path('./prompting') / prompt_path
    path = base / (name + '.md')
    if not path.exists():
        raise FileNotFoundError(
            f"File not found for {name}, looking for '{path}'",
            f' looking in directory: {base}')

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        msg = f'File not found for {name}, looking for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e


def read_dual_prompt(name: str, prompt_path: Path) -> DualPrompt:
    """
    Read a dual prompt from the provided path.
    """
    try:
        system = read_single_prompt(name + '_system', prompt_path)
        human = read_single_prompt(name + '_human', prompt_path)
        return DualPrompt(system, human)
    except FileNotFoundError as e:
        msg = f'File not found for {name}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e
