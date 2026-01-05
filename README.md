# MedBench-LLM-Summaries

## Overview

Welcome to the MedBench-LLM-Summaries repository. This repository contains Python code for generating summaries of Electronic Health Records (EHRs) using Large Language Models (LLMs) as part of the MedBench research study. The study aims to evaluate and improve the performance of LLMs in medical documentation tasks.

## Objectives

- **Summary Generation**: Utilize LLMs to generate accurate and comprehensive summaries of fictional EHRs.
- **Benchmarking**: Establish benchmarks to assess the quality and accuracy of LLM-generated summaries.
- **Evaluation**: Implement methods to quantitatively and qualitatively evaluate the generated summaries.

## Current Approaches

This repository implements multiple discharge summary generation approaches:

### 1. **Basic** (Default)
Direct prompting where the entire EHR is provided to the LLM with a structured prompt to generate comprehensive discharge summaries in a single shot.

### 2. **Reflection** (Agentic)
An agentic approach using iterative self-critique and refinement:
- Generator creates initial draft
- Critic evaluates completeness, accuracy, and coherence
- Refinement improves based on critique
- Iterates until quality threshold met (max 2 iterations)

### 3. **Hierarchical** (Future)
Multi-agent system with planning and specialization (under development).

**Note:** Previous approaches (map-reduce, decompose, refine) have been removed as they didn't show significant differences in performance compared to the basic approach.

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

#### Basic Approach (Single-Shot)
```bash
# Run with default settings (Medicine specialty, original language)
uv run python src/run_evaluation.py

# Customize the evaluation
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language Swedish \
    --model gpt-5.2 \
    --approach basic
```

#### Reflection Approach (Agentic)
```bash
# Use reflection for quality improvement
uv run python run_evaluation.py \
    --specialty Orthopaedics \
    --language English \
    --model gpt-5.2 \
    --approach reflection
```

#### See All Options
```bash
uv run python run_evaluation.py --help
```

### Output

All evaluations save:
- **Discharge summaries**: Text files in `data/output/<specialty>/`
- **Metadata summary**: `metadata_summary.json` with token counts, timing, and approach-specific metrics

**See [RUNNING_EVALUATIONS.md](RUNNING_EVALUATIONS.md) for detailed documentation, examples, and best practices.**

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

## Development

### Installing Dev Dependencies

```bash
uv sync --group dev
```

### Type Checking with mypy

Run type checks via `uv` to ensure the correct environment is used:

```bash
# Full project type-check
uv run mypy src

# Single file check (faster)
uv run mypy src/prompts/agentic/reflection.py

# Fresh run (ignore cached results)
uv run mypy --no-incremental src
```

### Linting and Formatting

```bash
# Format code
uv run black src

# Lint with flake8
uv run flake8 src

# Lint with pylint
uv run pylint src
```

## Contributing

We welcome contributions from the community. Please refer to our contribution guidelines for more information.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
