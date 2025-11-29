# Agentic Discharge Summary Generation

This module implements agentic architectures for discharge summary generation, designed for research comparison with baseline single-shot approaches.

## Research Motivation

Traditional LLM approaches use a single prompt to generate the entire discharge summary. This project explores whether **agentic workflows**—where multiple LLM instances collaborate through feedback loops and specialization—can produce higher quality medical documentation.

## Architectures Implemented

### 1. Reflection Agent (Simple Agentic)
**File:** `reflection.py`

A three-agent system with iterative improvement:
```
Generator → Critic → Refinement → (iterate) → Final Summary
```

**Agents:**
- **Generator:** Creates initial comprehensive draft
- **Critic:** Evaluates completeness, accuracy, redundancy, coherence, temporal consistency
- **Refinement:** Addresses specific critiques

**Agentic characteristics:**
- ✅ Self-evaluation through critic agent
- ✅ Iterative refinement based on feedback
- ✅ Dynamic stopping (when quality threshold met)

**Best for:** General improvement in accuracy and completeness

### 2. Hierarchical Multi-Agent (Complex Agentic)
**File:** `hierarchical.py` (⚠️ **Under Development**)

A coordinated system of specialized agents:
```
Orchestrator
    ↓
[Topic Identification] [Relationship Mapping] [Timeline]
    ↓
[Specialized Topic Agents per diagnosis]
    ↓
[Synthesis Agent]
    ↓
[QA Agent]
```

**Agents:**
- **Orchestrator:** Analyzes case complexity, plans decomposition strategy
- **Topic Identifier:** Extracts diagnoses and clinical problems
- **Relationship Mapper:** Identifies causal and temporal relationships
- **Topic Agents:** Generate focused content per diagnosis (specialized by domain)
- **Synthesis Agent:** Combines sections while maintaining coherence
- **QA Agent:** Final validation and revision triggering

**Agentic characteristics:**
- ✅ Autonomous planning (orchestrator decides strategy)
- ✅ Specialization (different agents for different topics)
- ✅ Tool use (structured data extraction)
- ✅ Multi-level feedback (QA triggers revisions)

**Best for:** Complex cases with multiple diagnoses and long hospital courses

## Usage

### Basic Usage (Reflection)

```python
from agentic import ReflectionAgent
from helpers import init_model, read_all_cases

# Initialize model and agent
model = init_model("gpt-4")
agent = ReflectionAgent(model, language="English", max_iterations=2)

# Load case
cases = read_all_cases("Orthopaedics", "English")
case = cases[0]

# Generate with reflection
result = agent.generate(case)

print(f"Summary: {result['summary']}")
print(f"Iterations: {result['iterations']}")
print(f"Critiques: {result['critiques']}")
```

### Comparing Approaches

```python
from basic import BasicGenerator
from agentic import ReflectionAgent, HierarchicalMultiAgent
from helpers import evaluate_summary

# Generate with all three approaches
basic_summary = BasicGenerator(model, language="English").generate(case)
reflection_summary = ReflectionAgent(model, language="English").generate(case)
hierarchical_summary = HierarchicalMultiAgent(model, language="English").generate(case)

# Compare quality
basic_score = evaluate_summary(basic_summary, reference)
reflection_score = evaluate_summary(reflection_summary['summary'], reference)
hierarchical_score = evaluate_summary(hierarchical_summary['summary'], reference)

print(f"Basic: {basic_score}")
print(f"Reflection: {reflection_score}")
print(f"Hierarchical: {hierarchical_score}")
```

## Research Questions

This implementation is designed to answer:

1. **Does agency improve quality?**
   - Comparison: Basic vs. Reflection
   - Metrics: Completeness, accuracy, clinical coherence

2. **Does complexity add value?**
   - Comparison: Reflection vs. Hierarchical
   - Metrics: Handling of multi-diagnosis cases, narrative flow

3. **Cost-benefit tradeoff?**
   - Metrics: Quality improvement vs. API cost (number of calls)
   - Analysis: When is agentic approach worth the overhead?

4. **What types of cases benefit most?**
   - Hypothesis: Complex cases benefit more from hierarchical approach
   - Analysis: Stratify by case complexity (simple vs. complex)

## Evaluation Framework

### Metrics

**Automated Metrics:**
- Completeness score (% of required sections filled)
- Factual accuracy (fact extraction + verification)
- Redundancy score (repeated n-grams)
- ICD-10 code accuracy
- Medication reconciliation accuracy

**Human Evaluation:**
- Clinical coherence (1-5 scale)
- Narrative flow (1-5 scale)
- Usability for handoff (1-5 scale)
- Overall preference (basic vs. agentic)

**Cost Metrics:**
- Total tokens used
- Number of API calls
- Latency (time to generate)

### Experimental Design

```
Dataset: MedBench cases (Orthopaedics, Surgery, Medicine)
n = 100 cases per specialty

Approaches:
- Baseline: Single-shot basic prompt
- Reflection: 2 iterations max
- Hierarchical: Full multi-agent

Evaluation:
- Automated metrics on all cases
- Human evaluation on random sample (n=30)
- Stratified analysis by case complexity
```

## Prompt Engineering

### Reflection Agent Prompts
- `prompts/English/reflection/generator_system.md` - Initial draft generation
- `prompts/English/reflection/critic_system.md` - Quality evaluation
- `prompts/English/reflection/refinement_system.md` - Revision based on critique

### Hierarchical Agent Prompts (TODO)
- `prompts/English/hierarchical/orchestrator_system.md`
- `prompts/English/hierarchical/topic_identifier_system.md`
- `prompts/English/hierarchical/topic_agent_system.md`
- `prompts/English/hierarchical/relationship_system.md`
- `prompts/English/hierarchical/synthesis_system.md`
- `prompts/English/hierarchical/qa_system.md`

## Development Status

| Component | Status | Notes |
|-----------|--------|-------|
| Reflection Agent | ✅ Implemented | Ready for testing |
| Reflection Prompts (English) | ✅ Complete | Tested |
| Reflection Prompts (Swedish) | 🚧 In Progress | Need translation |
| Hierarchical Agent | 🚧 In Progress | Skeleton complete, needs prompts |
| Hierarchical Prompts | ❌ Not Started | Requires design |
| Evaluation Framework | ❌ Not Started | Needs implementation |
| Integration with run_evaluation.py | ❌ Not Started | Needs update |

## Next Steps

### Phase 1: Validate Reflection (Current)
1. ✅ Implement reflection agent
2. ✅ Create English prompts
3. 🔲 Create Swedish prompts
4. 🔲 Test on sample cases
5. 🔲 Run pilot evaluation (n=10)
6. 🔲 Analyze iteration patterns (when does it converge?)

### Phase 2: Compare Reflection vs. Basic
1. Run full evaluation (n=100)
2. Compute automated metrics
3. Human evaluation
4. Cost analysis
5. Write up results

### Phase 3: Implement Hierarchical (If reflection shows promise)
1. Design hierarchical prompts
2. Implement full multi-agent system
3. Test on complex cases
4. Comparative evaluation

## References

**Agentic Design Patterns:**
- Reflection: Wang et al. (2023) "Self-Refine"
- Multi-agent: Wu et al. (2023) "AutoGen"
- Medical documentation: TBD (this research)

## Contributing

When adding new agents or prompts:
1. Follow the structure in `reflection.py` as template
2. Create both English and Swedish prompts
3. Document in this README
4. Add tests for new functionality
5. Update evaluation framework if new metrics needed
