from typing import Literal
from dataclasses import dataclass

from langchain_openai import AzureChatOpenAI
import tiktoken


@dataclass
class ModelDefinition:
    """
    A dataclass to store the model definition.

    Also provides a method to get a file description string for knowing what
    model was used to generate the text when saving the output.
    """
    deployment: str
    name: str
    version: str

    def get_id(self) -> str:
        """
        An id to identify the model used to generate the text.

        Used when saving the output to know what model was used to generate

        Returns:
            str: A string with the model name and version.
        """
        return f"{self.name}_{self.version}"


AvailableModels = Literal['gpt-35', 'gpt-4o-mini', 'gpt-4-turbo']

available_models: dict[AvailableModels, ModelDefinition] = {
    "gpt-35":
    ModelDefinition(
        deployment="gpt_35_16k",
        name="gpt-35-turbo-16k",
        version="0613",
    ),
    "gpt-4o-mini":
    ModelDefinition(
        deployment="gpt-4o-mini",
        name="gpt-4o-mini",
        version="2024-07-18",
    ),
    "gpt-4-turbo":
    ModelDefinition(
        deployment="gpt-4-turbo",
        name="gpt-4",
        version="turbo-2024-04-09",
    ),
}


def init_model(model_name: AvailableModels,
               temperature: float) -> tuple[AzureChatOpenAI, str]:
    """
    Initialize a language model for a given model name and temperature.

    Returns:
        tuple[AzureChatOpenAI, str]: A tuple containing the language model
        and a string to identify the model used to generate
    """
    model = available_models.get(model_name)
    if not model:
        raise ValueError(f"Model {model_name} not found")

    return AzureChatOpenAI(
        deployment_name=model.deployment,
        model_name=model.name,
        temperature=temperature,
    ), model.get_id() + f"@temp={temperature}"


def count_tokens(text: str, model_name: AvailableModels) -> int:
    """Count the number of tokens in the text for a specific model."""

    # Map models to known tokenizer encodings
    model_to_encoding = {
        "gpt-35-turbo-16k": "cl100k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4": "cl100k_base"
    }
    encoding_name = model_to_encoding.get(model_name)
    if not encoding_name:
        raise ValueError(f"Encoding not found for model {model_name}")
    encoding = tiktoken.get_encoding(encoding_name)

    tokens = encoding.encode(text)
    return len(tokens)
