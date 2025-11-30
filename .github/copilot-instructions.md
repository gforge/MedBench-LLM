# MedBench-LLM Copilot Instructions

## Project Overview
MedBench-LLM evaluates Large Language Models (LLMs) on medical discharge summary generation. It supports multiple approaches (Basic, Reflection) and handles multi-language medical records.

We have structered the cases so that each case has an original language (i.e. plain English using Snomed terms without any abbreviations). This case is then translated into other languages (e.g. Swedish) while maintaining the same structure and content. If the style is "clinical" then the text can contain abbreviations and more clinical jargon to resemble real-world clinical notes. In addition each case has a fact sheet where key facts are listed so that we can evaluate if the summary contained the key information.

## Architecture & Core Components

### Entry Point
- All code is under `src/`.
- `run_evaluation.py`: Main CLI entry point. Orchestrates the evaluation process:
  1. Parses arguments (`helpers.config`).
  2. Initializes the model (`helpers.init_model`).
  3. Loads cases (`helpers.read_all_cases`).
  4. Runs the evaluation loop (`helpers.evaluator.CaseEvaluator`).

### Key Modules
- **`helpers/`**: Shared utilities.
  - `case.py`: The `Case` class is the core data structure. It parses raw markdown into structured sections (progress notes, surgery, labs, meds). **Always use `Case` methods to access data.**
  - `init_model.py`: Manages Azure OpenAI model initialization and token counting.
  - `read_all_cases.py`: Loads cases from `data/processed/`.
  - `evaluator.py`: `CaseEvaluator` handles the processing loop, rate limiting, and result saving.
- **`basic/`**: Single-shot summarization approach.
  - `basic.py`: Implements the basic summarization chain.
- **`agentic/`**: Agentic approaches.
  - `reflection.py`: Implements the `ReflectionAgent` (Generator -> Critic -> Refinement loop).

### Data Flow
1. **Input**: Processed cases in `data/processed/merged/*.md` and `data/processed/markdown/*.json`.
2. **Processing**: `CaseEvaluator` iterates through cases, calling the selected `summarize_fn`.
3. **Output**: Generated summaries saved to `data/output/<specialty>/` as text files. Metadata aggregated in `metadata_summary.json`.

## Developer Workflows

### Running Evaluations
Use `uv` to run the evaluation script:
```bash
# Basic approach
uv run python src/run_evaluation.py --specialty Medicine --language original --approach basic

# Reflection approach
uv run python src/run_evaluation.py --specialty Surgery --language English --approach reflection --model gpt-4o-mini
```

### Dependency Management
- This project uses `uv` for dependency management.
- Install dependencies: `uv sync`
- Add dependencies: `uv add <package>`

### Configuration
- **Environment**: `.env` file required for Azure OpenAI credentials (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`).
- **Models**: Defined in `helpers/init_model.py`. Add new models to `available_models` dict.

## Coding Conventions

### Data Access
- **Do not parse raw text manually.** Use the `Case` object methods:
  - `case.progress_notes`: Get all progress notes.
  - `case.surgery`: Get surgery notes.
  - `case.initial_medications()`: Get admission meds.
  - `case.get_day(n)`: Get data for a specific day.

### Prompts
- Prompts are stored in `prompts/` directories within each module (`basic/prompts`, `agentic/prompts`).
- Organized by language: `English/`, `Swedish/`, etc.
- Use `helpers.read_prompt` utilities to load them.

### Logging & Output
- Use `logging.info()` for progress updates.
- `CaseEvaluator` handles standard logging and metadata tracking.
- **Do not print to stdout** inside library code; use the logger.

### Error Handling
- `CaseEvaluator` catches exceptions per case to prevent the entire batch from failing.
- Ensure `summarize_fn` raises exceptions for fatal errors so they can be logged properly.

## Common Patterns

### Adding a New Approach
1. Create a new module (e.g., `hierarchical/`).
2. Implement a summarize function or agent class.
3. Register it in `run_evaluation.py` inside `get_summarize_function`.
4. Add prompts to the module's `prompts/` directory.

### Modifying Model Config
- Edit `helpers/init_model.py` to update `available_models` or change token counting logic.
