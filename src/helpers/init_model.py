import logging
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from langchain_openai import AzureChatOpenAI

logger = logging.getLogger(__name__)


def _clean_azure_endpoint() -> None:
    """Clean the Azure OpenAI endpoint URL in environment variables.

    Removes any path components after the base URL (e.g., /openai/responses).
    The endpoint should be just the base URL like:
    - https://xxx.openai.azure.com/
    - https://xxx.cognitiveservices.azure.com/
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    if not endpoint:
        return

    # Match Azure OpenAI or Cognitive Services URLs and strip any path after the domain
    # Handles both *.openai.azure.com and *.cognitiveservices.azure.com
    match = re.match(
        r"(https?://[^/]+\.(?:openai|cognitiveservices)\.azure\.com)/?.*",
        endpoint,
        re.IGNORECASE,
    )
    if match:
        clean_endpoint = match.group(1) + "/"
        if clean_endpoint != endpoint:
            logger.warning(
                "AZURE_OPENAI_ENDPOINT contained extra path components. Cleaned URL from '%s' to '%s'",
                endpoint,
                clean_endpoint,
            )
            os.environ["AZURE_OPENAI_ENDPOINT"] = clean_endpoint


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
    tokenizer_encoding: str
    api_version: str | None = None

    def get_id(self) -> str:
        """
        An id to identify the model used to generate the text.

        Used when saving the output to know what model was used to generate

        Returns:
            str: A string with the model name and version.
        """
        return f"{self.name}_{self.version}"


AvailableModels = Literal[
    "gpt-5-mini",
    "gpt-5.1-chat",
    "gpt-5.2",
    "gpt-5.5",
]

available_models: dict[AvailableModels, ModelDefinition] = {
    "gpt-5-mini": ModelDefinition(
        deployment="gpt-5-mini",
        name="gpt-5-mini",
        version="2025-08-07",
        tokenizer_encoding="o200k_base",
    ),
    "gpt-5.1-chat": ModelDefinition(
        deployment="gpt-5.1",
        name="gpt-5.1",
        version="2025-11-13",
        tokenizer_encoding="o200k_base",
        api_version="2024-12-01-preview",
    ),
    "gpt-5.2": ModelDefinition(
        deployment="gpt-5.2",
        name="gpt-5.2",
        version="2025-12-11",
        tokenizer_encoding="o200k_base",
        api_version="2024-12-01-preview",
    ),
    "gpt-5.5": ModelDefinition(
        deployment="gpt-5.5",
        name="gpt-5.5",
        version="2026-04-24",
        tokenizer_encoding="o200k_base",
        api_version="2024-12-01-preview",
    ),
}


def get_model_definition(model_name: AvailableModels) -> ModelDefinition:
    """Fetch model definition and fail with a clear message if missing."""
    model = available_models.get(model_name)
    if not model:
        raise ValueError(f"Model {model_name} not found")
    return model


def validate_model_setup(model_name: AvailableModels) -> str:
    """Validate model and tokenizer configuration before processing cases.

    Returns:
        The tokenizer encoding name configured for the model.
    """
    model = get_model_definition(model_name)
    if not model.tokenizer_encoding:
        raise ValueError(
            f"Model {model_name} is missing tokenizer_encoding. "
            "Add tokenizer_encoding to available_models in src/helpers/init_model.py and update README model docs."
        )

    import tiktoken

    try:
        tiktoken.get_encoding(model.tokenizer_encoding)
    except Exception as exc:
        raise ValueError(
            f"Tokenizer encoding '{model.tokenizer_encoding}' for model {model_name} is not available. "
            "Update tokenizer_encoding in src/helpers/init_model.py before running evaluations."
        ) from exc

    return model.tokenizer_encoding


def init_model(model_name: AvailableModels, temperature: float) -> tuple["AzureChatOpenAI", str]:
    """
    Initialize a language model for a given model name and temperature.

    Returns:
        tuple[AzureChatOpenAI, str]: A tuple containing the language model
        and a string to identify the model used to generate
    """
    # Clean up the endpoint URL if it has extra path components
    _clean_azure_endpoint()

    from langchain_openai import AzureChatOpenAI

    model = get_model_definition(model_name)

    client_kwargs: dict[str, Any] = {
        "deployment_name": model.deployment,
        "model_name": model.name,
        "temperature": temperature,
    }
    if model.api_version:
        client_kwargs["api_version"] = model.api_version

    return (
        AzureChatOpenAI(**client_kwargs),
        model.get_id() + f"@temp={temperature}",
    )


def count_tokens(text: str, model_name: AvailableModels) -> int:
    """Count the number of tokens in the text for a specific model."""

    model = get_model_definition(model_name)
    if not model.tokenizer_encoding:
        raise ValueError(
            f"Encoding not found for model {model_name}. "
            "Set tokenizer_encoding in src/helpers/init_model.py available_models."
        )

    import tiktoken

    encoding = tiktoken.get_encoding(model.tokenizer_encoding)

    tokens = encoding.encode(text)
    return len(tokens)
