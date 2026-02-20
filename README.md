# Reliable AI Writing Systems Challenge Showcase

Welcome to my submission for the Reliable AI Writing Systems challenge. This repository contains a prototype for detecting and eliminating hallucinations in long-form AI writing.

## The Core Problem: Strategic Drift & Intrinsic Errors

When you task an LLM to write a 5 to 20-page research report based on provided documents, the core problem isn't just the AI inventing random facts. The fundamental root cause is what we call **Strategic Drift**. As a model generates a massive amount of text, its attention mechanism degrades. It begins to condition heavily on its own newly generated text rather than the original source constraints.

Because of this, the most critical failure mode we must solve is the **Intrinsic Faithfulness Error**—cases where the LLM actively misrepresents or contradicts the grounded source material. Users can forgive an AI that admits it doesn't know something, but they will instantly lose trust in a system that confidently breaks the facts they uploaded.

## The Trade-off & Why Approach 2 (Tool-Made LLM Eval)

To solve this, we had to make a fundamental trade-off: We are explicitly trading off compute cost and baseline generation latency to guarantee maximum factual accuracy.

With that trade-off in mind, we faced a choice between two main architectures:

- **Approach 1: Multi-Agent Debate**, where multiple LLMs argue back and forth about the truthfulness of the generated text.
- **Approach 2: Tool-Made LLM Eval**, where a dedicated Evaluator LLM is equipped with tools to verify claims.

We completely rejected Approach 1. For a 20-page document, passing the entire source context and the generated draft back and forth between agents creates prohibitive token costs and latency that scales terribly in a production environment. Furthermore, pumping 100k tokens into a judge LLM triggers the "Lost in the Middle" problem, where the evaluating agent itself begins to hallucinate.

Instead, we chose **Approach 2: Tool-Made LLM Eval**. In this architecture, we decouple fluency from truth. The Generator LLM focuses solely on writing the report. Meanwhile, a completely separate Evaluator LLM acts as an isolated judge. Rather than reading the entire source text, the Evaluator reads the draft sentence by sentence, extracts active claims, and uses a bounded `VectorSearch` tool to retrieve the exact, tiny chunk of truth needed to verify that specific claim.

## The Evaluation Rubric & Prototype Showcase

For our evaluation rubric to be defensible, we define ground truth _strictly_ as the user's provided context. If a claim cannot be found in the local vectors by the search tool, it is flagged as a hallucination—even if it's generally true in the real world. Our system is tuned to prioritize precision over recall; it is far better to falsely flag a truthful statement (a false positive) than to let a hallucination slip through to the end user.

In our prototype showcase, the orchestrator passes a generated chunk to the Evaluator. The Evaluator formulates a query, hits the Vector Database to pull up facts, and issues a strict _Pass_ or _Fail_ grade along with a rationale. This prevents unverified claims from sneaking into the final document.

## Validation Plan: The "Needle in the Haystack" Sabotage

Of course, a prototype is just the beginning. If we had two weeks to validate this approach before scaling, the very first thing we must test is the tool's efficacy itself. We call this the "Needle in the Haystack" Sabotage.

We would inject 200 known contradictions into perfect reports and see if the Evaluator can formulate the right search queries to retrieve the contradictory chunk. We test this first because the entire architecture rests on the assumption that the semantic search tool returns relevant snippets. If the vector search fails to pull the right data, the Evaluator is essentially blind. We must validate that the tool works before we worry about the LLM's grading logic.

## Next Steps for Production Readiness

More info in [file:proposal/next-steps.md]

Looking ahead, we have a clear engineering roadmap to evolve this from a Python proof-of-concept to a production-grade application that hits our strict latency constraints:

1. **Asynchronous Concurrent Evaluation**: Evaluating chunks sequentially in a loop takes way too long. By using asynchronous API calls under a concurrency semaphore, we can evaluate dozens of draft sections simultaneously, reducing the evaluation bottleneck from minutes to just seconds.
2. **Iterative Long-form Generation**: To arrest Strategic Drift at the source, the LLM will first generate a dedicated Outline. We will then iterate through that outline to generate and evaluate the document section by section, ensuring the AI never carries too much of its own generated baggage at once.
3. **Semantic Chunking**: We'll upgrade from naive text splitting to a robust semantic chunking strategy, ensuring the Evaluator is always looking at complete logical thoughts.

By aggressively enforcing factual anchoring with a tool-based evaluator, we can build a long-form generation system that our users can actually trust.

---

## Navigating the Showcase

Please navigate to the **`proposal/`** directory to review the showcase in its entirety. It contains:

1. **`proposal/hallucination-research-proposal.md`**: The comprehensive research proposal (Problem Decomposition, Evaluation Rubric, Architecture, Validation Plan).
2. **`proposal/scenario/`**: Ground-truth data and a mocked hallucinated generation.
3. **`proposal/src/scenario.py`**: A Python script demonstrating the Evaluator LLM using Vector Search to catch the hallucinations in real-time, run in a virtual environment.
4. **`proposal/tests/`**: Automated tests verifying the evaluator agent's logic.

For a detailed walkthrough of the implementation, start by reading **`proposal/README.md`**.
