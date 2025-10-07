# MedBench-LLM-Summaries

## Overview

Welcome to the MedBench-LLM-Summaries repository. This repository contains Python code for generating summaries of Electronic Health Records (EHRs) using Large Language Models (LLMs) as part of the MedBench research study. The study aims to evaluate and improve the performance of LLMs in medical documentation tasks.

## Objectives

- **Summary Generation**: Utilize LLMs to generate accurate and comprehensive summaries of fictional EHRs.
- **Benchmarking**: Establish benchmarks to assess the quality and accuracy of LLM-generated summaries.
- **Evaluation**: Implement methods to quantitatively and qualitatively evaluate the generated summaries.

## Current Approach

This repository implements a **Basic** direct prompting approach where the entire EHR is provided to the LLM with a structured prompt to generate comprehensive discharge summaries.

Previous approaches (map-reduce, decompose, refine) have been removed as they didn't show significant differences in performance compared to the basic approach.

## Usage

### Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Configure your Azure OpenAI credentials in a `.env` file:
   ```bash
   # Add your Azure OpenAI credentials
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   ```

### Running Evaluations

You can run the evaluation using `uv run`:

```bash
# Run with default settings (Medicine specialty, original language, gpt-4-turbo)
uv run python run_evaluation.py

# Or using the shorter form
uv run run_evaluation.py

# Customize the evaluation with command-line arguments
uv run python run_evaluation.py --specialty Surgery --language Swedish --model gpt-4o-mini

# See all available options
uv run python run_evaluation.py --help
```

**Available Options:**
- `--specialty`: Medical specialty to filter cases (default: Medicine)
- `--language`: Language filter (default: original)
- `--model`: LLM model to use (choices: gpt-35, gpt-4o-mini, gpt-4-turbo)
- `--temperature`: Temperature for generation (default: 0.0)
- `--rate-limit`: Seconds between API calls (default: 60)
- `--approach`: Summarization approach (default: basic)

### Data Preparation

Prepare the EHR data in the specified format under `data/processed/`.

### Evaluation

Use the MedBench platform to evaluate the generated summaries found in `data/output/`.

## Contributing

We welcome contributions from the community. Please refer to our contribution guidelines for more information.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
