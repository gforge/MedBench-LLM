import json

from .Case import Case


def read_markdown_file(path: str) -> str:
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError as e:
        msg = f'File not found for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e


def read_json_file(path: str) -> Case:
    try:
        with open(path, 'r') as file:
            data = json.load(file)
            # Convert filename "markdown_Cardiology_Case 1_original.json"
            # to id = "Cardiology_Case 1"
            # language = "original"
            filename = path.split('/')[-1]
            filename = filename.replace('markdown_', '').replace('.json', '')
            data['language'] = filename.split('_')[-1]
            data['id'] = '_'.join(filename.split('_')[:-1])

            return Case(**data)

    except FileNotFoundError as e:
        msg = f'File not found for {path}'
        raise FileNotFoundError(f"{str(e)}: {msg}") from e
