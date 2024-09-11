from dataclasses import dataclass
from pathlib import Path


@dataclass
class DualPrompt:
    """
    Represents a dual prompt with two different prompts.
    """
    system: str
    human: str


prompt_cache = {}


def read_single_prompt(name: str, prompt_path: Path, language: str) -> str:
    """
    Read a single prompt from the provided path.

    Args:
    - name: Name of the prompt file to read.
    - prompt_path: Path to the prompt directory.
    """
    key = f'{name}_{str(prompt_path)}_{language}'
    if key in prompt_cache:
        return prompt_cache[key]

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt directory not found at {prompt_path}")

    language_path = prompt_path / language
    if not language_path.exists():
        if language.lower() == 'original':
            language_path = prompt_path / "English"

        if not language_path.exists():
            raise FileNotFoundError(
                f"Language directory not found at {language_path}")

    base = Path('./prompting') / language_path
    path = base / (name + '.md')
    if not path.exists():
        raise FileNotFoundError(
            f"File not found for {name}, looking for '{path}'",
            f' looking in directory: {base}')

    try:
        with open(path, 'r', encoding='utf-8') as f:
            prompt_txt = f.read()
            prompt_cache[key] = prompt_txt
            return prompt_txt
    except FileNotFoundError as e:
        msg = f'File not found for {name}, looking for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e


def read_dual_prompt(
    name: str,
    prompt_path: Path,
    language: str,
) -> DualPrompt:
    """
    Read a dual prompt from the provided path.
    """
    try:
        system = read_single_prompt(name + '_system',
                                    prompt_path=prompt_path,
                                    language=language)
        human = read_single_prompt(name + '_human',
                                   prompt_path=prompt_path,
                                   language=language)
        return DualPrompt(system, human)
    except FileNotFoundError as e:
        msg = f'File not found for {name}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e
