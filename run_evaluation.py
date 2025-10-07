#! /usr/bin/env python
"""Main entry point for running LLM evaluation on medical cases."""

import logging

from dotenv import load_dotenv
from langchain.globals import set_verbose

from basic.basic import summarize
from helpers import (
    CaseEvaluator,
    EvaluationConfig,
    init_model,
    parse_args,
    read_all_cases,
)

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

    # Create evaluator and run
    evaluator = CaseEvaluator(
        config=config,
        llm=llm,
        model_id=model_id,
        summarize_fn=summarize,
    )

    evaluator.run(case_dict)


if __name__ == "__main__":
    main()
