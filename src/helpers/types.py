"""
Type definitions for language and style used across the codebase.

Language represents the actual language of the case (English, Swedish, Icelandic, etc.)
Style represents how the content is written:
  - plain: No abbreviations, uses SNOMED terms, universally understandable
  - clinical: Hospital-style with locale-specific abbreviations
"""

from typing import Literal

SUPPORTED_LANGUAGES = ("English", "Swedish", "Icelandic")

# The actual language of the case
Language = Literal["English", "Swedish", "Icelandic"]

# How the content is written
Style = Literal["plain", "clinical"]

# Valid language inputs (including 'original' which maps to English + plain)
LanguageInput = Literal[
    "original",
    "English",
    "Swedish",
    "Icelandic",
    "English-clinical",
    "Swedish-clinical",
    "Icelandic-clinical",
]


def parse_language_input(value: str) -> tuple[Language, Style]:
    """
    Parse a language input string into (Language, Style) tuple.

    Args:
        value: Input string like 'original', 'English', 'Swedish-clinical', etc.

    Returns:
        Tuple of (Language, Style)

    Examples:
        >>> parse_language_input('original')
        ('English', 'plain')
        >>> parse_language_input('English')
        ('English', 'plain')
        >>> parse_language_input('Swedish-clinical')
        ('Swedish', 'clinical')
    """
    value = value.strip()

    # Handle 'original' as English + plain
    if value.lower() == "original":
        return ("English", "plain")

    # Check for compound format: Language-Style
    if "-" in value:
        parts = value.split("-", 1)
        lang = parts[0].capitalize()
        style = parts[1].lower()

        if lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {lang}")
        if style not in ("plain", "clinical"):
            raise ValueError(f"Unsupported style: {style}")

        return (lang, style)  # type: ignore[return-value]

    # Simple language name defaults to plain style
    lang = value.capitalize()
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}")

    return (lang, "plain")  # type: ignore[return-value]
