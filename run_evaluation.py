#! /usr/bin/env python
"""Main entry point for running LLM evaluation on medical cases."""

import logging

from dotenv import load_dotenv
from langchain.globals import set_verbose

from agentic.reflection import ReflectionAgent
from basic.basic import summarize
from helpers import (
    CaseEvaluator,
    EvaluationConfig,
    init_model,
    parse_args,
    read_all_cases,
)
from helpers.case import Case

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Suppress verbose loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
set_verbose(False)

# Load environment variables (Azure credentials, etc.)
load_dotenv()


def get_summarize_function(approach: str, llm, language: str):
    """Get the appropriate summarize function for the specified approach.

    Args:
        approach: The approach to use ("basic", "reflection", "hierarchical")
        llm: The language model instance
        language: The language for prompts

    Returns:
        A function that takes (llm, language, text) and returns summary or result dict
    """
    if approach == "basic":
        return summarize
    elif approach == "reflection":
        agent = ReflectionAgent(llm, language, max_iterations=2)

        def reflection_wrapper(llm, language, text):
            # Convert text to Case object (basic case with just notes)
            case = Case(
                language=language,
                case_id="temp",
                specialty="",
                notes_raw=text,
            )
            return agent.generate(case)

        return reflection_wrapper
    elif approach == "hierarchical":
        raise NotImplementedError("Hierarchical approach not yet implemented")
    else:
        raise ValueError(f"Unknown approach: {approach}")


def main():
    """Main function to run the evaluation."""
    # Parse command-line arguments and create configuration
    args = parse_args()
    config = EvaluationConfig.from_args(args)

    logging.info("Starting evaluation with configuration:")
    logging.info("  Specialty: %s", config.specialty)
    logging.info("  Language: %s", config.language)
    logging.info("  Model: %s", config.model_name)
    logging.info("  Temperature: %.1f", config.temperature)
    logging.info("  Approach: %s", config.approach)

    # Validate data directory exists
    if not config.data_dir.exists():
        raise FileNotFoundError(f"Cases directory not found at {config.data_dir}")

    # Initialize the language model
    llm, model_id = init_model(config.model_name, temperature=config.temperature)
    logging.info("Initialized model: %s", model_id)

    # Load cases
    case_dict = read_all_cases(
        base_dir=config.data_dir,
        filter_specialty=config.specialty,
        filter_language=config.language,
    )
    logging.info("Loaded %d cases", len(case_dict))

    if len(case_dict) == 0:
        logging.warning("No cases found matching the specified filters.")
        return

    # Get the appropriate summarize function for the approach
    summarize_fn = get_summarize_function(config.approach, llm, config.language)

    # Create evaluator and run
    evaluator = CaseEvaluator(
        config=config,
        llm=llm,
        model_id=model_id,
        summarize_fn=summarize_fn,
    )

    evaluator.run(case_dict)


if __name__ == "__main__":
    main()
