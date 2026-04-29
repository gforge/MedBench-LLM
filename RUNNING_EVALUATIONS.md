# Running Evaluations

This document describes how to run discharge summary evaluations with different approaches.

## Quick Start

### Basic Approach (Single-Shot)
```bash
uv run python src/run_evaluation.py

# Or provide flags explicitly
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language English \
    --approach basic
```

### Reflection Approach (Agentic with Self-Critique)
```bash
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language English \
    --approach reflection
```

## Available Approaches

| Approach | Description | API Calls | Best For |
|----------|-------------|-----------|----------|
| `basic` | Single-shot generation | 1 per case | Fast, simple cases |
| `reflection` | Iterative with critic & refinement | ~3-7 per case | Quality improvement, research |

## Command-Line Options

```bash
uv run python src/run_evaluation.py \
  --specialty <specialty> \      # Medical specialty filter
  --language <language> \        # One language, comma-separated languages, or all
  --model <model> \              # LLM model from helpers.init_model.available_models
  --temperature <temp> \         # Temperature (0.0 = deterministic)
  --approach <approach> \        # Approach (basic, reflection)
  --require-complete-language-set <yes|no|auto> \  # Keep only case IDs present in all selected languages
  --rate-limit <seconds>          # Seconds between API calls
```

If `--specialty`, `--language`, `--model`, or `--approach` are omitted, the CLI prompts you to choose from the currently available options. Specialty and language prompts are derived from files in `data/processed/merged/`, language options show `original` first, and specialty counts are shown as unique cases.

### Examples

**Swedish Orthopedics with Reflection:**
```bash
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language Swedish \
    --approach reflection \
    --model gpt-5.1-chat
```

**Compare two languages on paired cases only:**
```bash
uv run python src/run_evaluation.py \
  --specialty Medicine \
  --language Swedish,English \
  --require-complete-language-set yes \
  --approach basic
```

**All Surgery Cases (Basic):**
```bash
uv run python src/run_evaluation.py \
    --specialty Surgery \
    --language original \
    --approach basic \
    --temperature 0.0
```

## Output

All approaches save results to: `data/output/<specialty>/`

### Files Generated

1. **Discharge Summaries**: `Summary_4_<case_id>@<language>@$<model>@<approach>.txt`
   - The actual generated discharge summary text

2. **Metadata Summary**: `metadata_summary.json`
   - Token counts (input, output, total)
   - Timing information (latency per case)
   - Approach-specific metrics (e.g., iterations for reflection)
   - Per-case details

### Example `metadata_summary.json`

```json
{
  "approach": "reflection",
  "model": "gpt-5.2_2025-12-11",
  "total_cases": 10,
  "successful_cases": 10,
  "failed_cases": 0,
  "total_tokens": 45230,
  "total_latency_seconds": 123.4,
  "average_latency_seconds": 12.3,
  "total_iterations": 15,
  "total_api_calls": 46,
  "average_iterations": 1.5,
  "average_api_calls": 4.6,
  "cases": [
    {
      "case_id": "case_001",
      "approach": "reflection",
      "latency_seconds": 15.2,
      "input_tokens": 2340,
      "output_tokens": 890,
      "total_tokens": 3230,
      "num_api_calls": 4,
      "iterations": 1,
      "critiques": ["..."]
    }
  ]
}
```

## Comparing Approaches

To compare different approaches, run them separately and analyze the metadata:

```bash
# Run basic
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language English \
    --approach basic

# Run reflection
uv run python src/run_evaluation.py \
    --specialty Orthopaedics \
    --language English \
    --approach reflection

# Compare the metadata_summary.json files
```

### Analysis Script (Example)

```python
import json
from pathlib import Path

# Load metadata from both approaches
basic_meta = json.load(open("data/output/Orthopaedics/metadata_summary.json"))
reflection_meta = json.load(open("data/output/Orthopaedics/metadata_summary.json"))

# Compare metrics
print(f"Basic - Tokens: {basic_meta['total_tokens']}, Time: {basic_meta['total_latency_seconds']:.1f}s")
print(f"Reflection - Tokens: {reflection_meta['total_tokens']}, Time: {reflection_meta['total_latency_seconds']:.1f}s")
print(f"Token increase: {(reflection_meta['total_tokens'] / basic_meta['total_tokens'] - 1) * 100:.1f}%")
print(f"Time increase: {(reflection_meta['total_latency_seconds'] / basic_meta['total_latency_seconds'] - 1) * 100:.1f}%")
```

## Token Tracking

All approaches now automatically track:
- **Input tokens**: From clinical notes
- **Output tokens**: Generated summary
- **Total tokens**: Sum of input + output
- **Latency**: Wall-clock time per case

This information is:
- Logged in real-time during processing
- Saved to `metadata_summary.json`
- Aggregated across all cases

### Token Costs

Use the metadata to estimate costs:

```python
# Example: OpenAI pricing (as of 2024)
INPUT_COST_PER_1K = 0.0015  # $0.0015 per 1K input tokens
OUTPUT_COST_PER_1K = 0.002  # $0.002 per 1K output tokens

metadata = json.load(open("data/output/Orthopaedics/metadata_summary.json"))

input_cost = (sum(c["input_tokens"] for c in metadata["cases"]) / 1000) * INPUT_COST_PER_1K
output_cost = (sum(c["output_tokens"] for c in metadata["cases"]) / 1000) * OUTPUT_COST_PER_1K
total_cost = input_cost + output_cost

print(f"Total cost: ${total_cost:.2f}")
print(f"Cost per case: ${total_cost / metadata['total_cases']:.2f}")
```

## Reflection Approach Details

The reflection approach uses a 3-agent system:

1. **Generator**: Creates initial draft
2. **Critic**: Evaluates completeness, accuracy, redundancy, coherence
3. **Refinement**: Improves based on critique

### Iterations

- Default: Max 2 iterations
- Stops early if critic marks as "ACCEPTABLE"
- Each iteration = 1 generator call + multiple critic/refinement calls

### Logged Information

```
Processing case case_001...
  reflection...
  ✓ Completeness: 0.95, Accuracy: 0.92, Time: 15.2s
    └─ Iterations: 1, API calls: 4
```

## Troubleshooting

### "No cases found"
- Check that `data/processed/` contains cases for the specialty/language
- Verify spelling of specialty (e.g., "Orthopaedics" not "Orthopedics")

### Rate limiting errors
- Increase `--rate-limit` value (default: 60 seconds)
- Check Azure OpenAI quota/limits

### "Hierarchical approach not yet implemented"
- Use `basic` or `reflection` instead
- See `agentic/RESEARCH_NOTES.md` for future roadmap

## Best Practices

1. **Start with basic** to verify setup works
2. **Use reflection** for quality-focused research
3. **Set temperature=0.0** for reproducibility
4. **Monitor metadata** to track costs
5. **Run small batches first** (filter by specialty)

## For Research Papers

When comparing approaches:
- ✅ Run both approaches on **same cases**
- ✅ Use **same model and temperature**
- ✅ Save metadata for cost-benefit analysis
- ✅ Document settings in paper (model version, temperature, max iterations)
- ✅ Report both quality metrics AND computational costs

See `agentic/RESEARCH_NOTES.md` for research design guidance.
