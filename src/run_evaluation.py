#! /usr/bin/env python
"""Main entry point for running LLM evaluation on medical cases."""

import logging

from dotenv import load_dotenv
from langchain_core.globals import set_verbose

from helpers import CaseEvaluator, EvaluationConfig, SummarizeFn, init_model, parse_args, read_all_cases
from prompts.agentic.reflection import summarize as reflection_summarize
from prompts.basic.basic import summarize as basic_summarize

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


def get_summarize_function(approach: str) -> SummarizeFn:
    """Get the appropriate summarize function for the specified approach.

    Args:
        approach: The approach to use ("basic", "reflection", "hierarchical")

    Returns:
        A SummarizeFn that takes (llm, language, case) and returns SummarizeResult
    """
    if approach == "basic":
        return basic_summarize
    elif approach == "reflection":
        return reflection_summarize
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
    logging.info("  Languages: %s", ", ".join(config.languages))
    logging.info(
        "  Require complete language set: %s",
        "yes" if config.require_complete_language_set else "no",
    )
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
        filter_languages=config.languages,
        require_all_languages_for_case=config.require_complete_language_set,
    )
    logging.info("Loaded %d cases", len(case_dict))

    if len(case_dict) == 0:
        logging.warning("No cases found matching the specified filters.")
        return

    # Get the appropriate summarize function for the approach
    summarize_fn = get_summarize_function(config.approach)

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
