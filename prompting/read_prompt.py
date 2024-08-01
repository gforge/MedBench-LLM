from dataclasses import dataclass
from pathlib import Path


@dataclass
class DualPrompt:
    system: str
    human: str


def read_single_prompt(name: str, prompt_path: str | Path = 'prompts') -> str:
    base = Path('./prompting') / prompt_path
    path = base / (name + '.md')
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError as e:
        msg = f'File not found for {name}, looking for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e


def read_dual_prompt(name: str) -> DualPrompt:
    try:
        system = read_single_prompt(name + '_system')
        human = read_single_prompt(name + '_human')
        return DualPrompt(system, human)
    except FileNotFoundError as e:
        msg = f'File not found for {name}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e
