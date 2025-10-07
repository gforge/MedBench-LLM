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

1. **Setup**: Install the required dependencies using `uv sync`.
2. **Data Preparation**: Prepare the EHR data in the specified format under `data/`.
3. **Run Summarization**: Use `run_evaluation.py` to generate summaries from the EHR data.
4. **Evaluation**: Use the MedBench platform to evaluate the generated summaries.

## Contributing

We welcome contributions from the community. Please refer to our contribution guidelines for more information.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
