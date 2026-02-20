# Anti-Hallucination Showcase: Approach 2 (Tool-Made LLM Eval)

Welcome to the Anti-Hallucination Showcase. This repository contains a complete, functioning proposal and implementation designed to address the problem of hallucinations in long-form AI writing, specifically tailored for a production application serving ~10,000 users generating research reports and analytical summaries.

## Getting Started

This showcase focuses entirely on **Approach 2: Tool-Made LLM Eval**. Instead of relying on a single LLM to generate and verify its own text (which often fails due to parametric memory limitations), this architecture separates generation from evaluation. It equips an independent Evaluator LLM with vector search tools to rigorously check facts against a local, dynamically generated knowledge base.

### Navigating the Showcase

1. **The Research Proposal**: Start by reading `hallucination-research-proposal.md`. This document breaks down the problem, defines a strict evaluation rubric, explains the chosen architecture, and outlines the validation plan.
2. **The Scenario Data**: Check out `scenario/source_knowledge.txt` (the ground truth data) and `scenario/mocked_generation.md` (a realistically flawed LLM output with injected hallucinations).
3. **The Codebase**: Our implementation lives in `src/`. It features an orchestrator, an evaluator agent, and a tool registry, all built with `litellm` and `chromadb`.
4. **The Scenario Walkthrough**: Run `python src/scenario.py` in your virtual environment for a step-by-step demonstration of the Evaluator Agent catching hallucinations in real time using vector search.
5. **Automated Tests**: Explore `tests/` to see how we programmatically verify the evaluator's accuracy against known false claims.

## Running the Code

To execute the scenario script or the automated tests, ensure you have set up a Python virtual environment and installed the dependencies listed in the root of the project.

```bash
# Example setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then, you can execute the scenario by running `python src/scenario.py` or run `pytest tests/` to execute the automated evaluation tests.
