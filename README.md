# MedBench-LLM-Summaries

## Overview

Welcome to the MedBench-LLM-Summaries repository. This repository contains Python code for generating summaries of Electronic Health Records (EHRs) using Large Language Models (LLMs) as part of the MedBench research study. The study aims to evaluate and improve the performance of LLMs in medical documentation tasks.

## Objectives

- **Summary Generation**: Utilize LLMs to generate accurate and comprehensive summaries of fictional EHRs.
- **Benchmarking**: Establish benchmarks to assess the quality and accuracy of LLM-generated summaries.
- **Evaluation**: Implement methods to quantitatively and qualitatively evaluate the generated summaries.

> **Full Pipeline:** This repository handles **Step 3** of the MedBench pipeline (LLM inference). For the complete workflow including data preparation (Steps 1–2), platform evaluation (Step 5), and automated metrics (Step 6), see the [MedBench DataPrep README](../DataPrep/README.md).

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

2. Configure your Azure OpenAI credentials in a `.env` file (go to https://ai.azure.com/foundryProject/overview):
   ```bash
   # Add your Azure OpenAI credentials
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   ```

### Running Evaluations

#### Basic Approach (Single-Shot)
```bash
# Run interactively and choose from available specialties/languages
uv run python src/run_evaluation.py

# Customize the evaluation
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
  --language Swedish,English \
    --model gpt-5.2 \
  --approach basic \
  --require-complete-language-set yes
```

#### Reflection Approach (Agentic)
```bash
# Use reflection for quality improvement
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language English \
    --model gpt-5.2 \
    --approach reflection
```

#### See All Options
```bash
uv run python src/run_evaluation.py --help
```

### Output

All evaluations save:
- **Discharge summaries**: Text files in `data/output/<specialty>/`
- **Metadata summary**: `metadata_summary.json` with token counts, timing, and approach-specific metrics

**See [RUNNING_EVALUATIONS.md](RUNNING_EVALUATIONS.md) for detailed documentation, examples, and best practices.**

**Available Options:**
- Running without `--specialty`, `--language`, `--model`, or `--approach` opens an interactive picker.
- `--specialty`: Medical specialty to filter cases (discovered from `data/processed/merged/`)
- `--language`: Language filter (one value, comma-separated values, or `all`; `original` is shown first in interactive mode)
- `--model`: LLM model to use (choices are taken from `helpers.init_model.available_models`, currently including `gpt-5-mini`, `gpt-5.1-chat`, `gpt-5.2`, and `gpt-5.5`)
- `--temperature`: Temperature for generation (default: 0.0)
- `--rate-limit`: Seconds between API calls (default: 60)
- `--approach`: Summarization approach to use (interactive if omitted)
- `--require-complete-language-set`: For multi-language runs, keep only case IDs that exist in all selected languages (`yes`, `no`, or `auto`; default `auto`)

### Data Preparation

Before running LLM inference, the EHR data must be prepared via the **MedBench DataPrep pipeline**. This populates the `data/processed/` directory with processed case files in markdown format.

#### Prerequisites

Before proceeding with LLM inference, ensure the following steps have been completed in the [MedBench/DataPrep](../DataPrep/) repository:

**✓ Step 1: Download charts from the Platform**
- **Requires**: Platform running (dev or production), admin account
- **Command**:
  ```bash
  cd ../DataPrep
  python download_platform_charts.py \
      --url https://label.cairlab.ki.se/graphql \
      --email admin@example.com
  ```
- **Output**: `data/output/allData.json`

**✓ Step 2: Convert charts to LLM input**
- **Requires**: R with packages: `tidyverse`, `glue`, `magrittr`, `lubridate`, `officer`, `readxl`, `jsonlite`, `knitr`, `snakecase`
- **Command**:
  ```bash
  cd ../DataPrep
  Rscript build_processed_output.R
  ```
- **Outputs** (3 formats per case):
  - `data/processed/raw/raw_{Specialty}_{CaseID}_{Language}.json` — Full structured data
  - `data/processed/markdown/markdown_{Specialty}_{CaseID}_{Language}.json` — Tables as markdown
  - `data/processed/merged/merged_{Specialty}_{CaseID}_{Language}.md` — **LLM input** (used here)
- **Next**: Copy processed data to LLM repo:
  ```bash
  rsync -a ../DataPrep/data/processed/ ./data/processed/
  ```

#### Validation Checklist

Before running LLM inference, confirm:
- ✓ Platform is accessible (or `data/output/allData.json` already exists)
- ✓ R environment has required packages installed
- ✓ `data/processed/merged/` contains markdown files (`merged_*.md`)
- ✓ At least one specialty has data for your target language

**For detailed DataPrep instructions, see the [MedBench DataPrep README](../DataPrep/README.md).**

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
