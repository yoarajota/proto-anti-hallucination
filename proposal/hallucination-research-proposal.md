# Hallucination Research Proposal: Tool-Made LLM Eval

## 1. Problem Decomposition

Hallucinations in long-form AI writing are not a monolith; they represent distinct failure modes in how an LLM retrieves, processes, and presents information. In the context of generating 5-20 page research reports and technical documentation, these failures can be decomposed into three primary categories:

1.  **Intrinsic Faithfulness Errors (Contradictions):** The LLM is provided with factual source material but contradicts it. For example, the source says "Q3 revenue grew by 15%", but the LLM writes "Q3 revenue declined by 15%." This is a failure of reading comprehension and faithful summarization.
2.  **Extrinsic Factuality Errors (Fabrications):** The LLM generates information that is completely absent from the source material. It relies on its parametric memory, which may be outdated or incorrect. For example, inventing a fictional quote from a CEO that wasn't in the provided transcript.
3.  **Contextual Misattributions (Logical Leaps):** The LLM correctly states facts but links them in a way that implies false causation or attributes them to the wrong entity within the text.

**Root Cause Analysis:**
The fundamental cause of these issues in long-form generation is "Strategic Drift." When a single LLM is tasked with being highly creative (generating 10 pages of varied, fluent text) and highly precise (staying perfectly anchored to a 50-page source document), its attention mechanism degrades. As the generation lengthens, the model conditions heavily on its own newly generated text rather than the original source constraints, leading to a drift away from ground truth.

**What matters most:** For a production system generating research reports, **Intrinsic Faithfulness Errors** are the most critical. Users can tolerate a system that occasionally refuses to generate an answer because it lacks information, but they cannot tolerate a system that confidently misrepresents the data they uploaded.

## 2. Evaluation Rubric

To solve hallucinations, we must separate the measurement of "fluency" from the measurement of "truth." Our evaluation rubric prioritizes precision over recall: it is better to falsely flag a correct statement as a hallucination (false positive) than to let a hallucination reach the user (false negative).

**Success Definition:** "Solved" means the system catches 99% of injected Intrinsic Faithfulness Errors against a provided source text, while maintaining a false-positive rate below 5% to avoid frustrating users with constant regeneration loops.

**Metrics:**

1.  **Faithfulness Rate:** The percentage of claims in the generated text that can be directly logically deduced from the provided source context. (Target: > 98%)
2.  **Evaluator Precision:** When the system flags a sentence as a hallucination, how often is it actually a hallucination? (Target: > 95%)
3.  **Evaluator Recall:** Out of all actual hallucinations present in the generated text, how many did the system catch? (Target: > 99%)

**Trade-offs:** We are explicitly trading off **Compute Cost and Latency** for **Accuracy**. A system that achieves >99% recall on hallucinations will require multiple LLM calls per generation. We accept that a 15-second generation might take 30 seconds if it ensures factual perfection.

**Ground Truth Establishment:** Ground truth is defined _strictly_ as the information contained within the user-provided "one-shot" context (the uploaded documents or retrieved database records). If a claim cannot be verified against this specific local context, it is deemed a hallucination, regardless of whether it is generally true in the real world.

## 3. Proposed Architecture: Tool-Made LLM Eval

To address Strategic Drift and enforce our rigid definition of ground truth, we propose a **Tool-Made LLM Eval** architecture.

**The Architecture:**

1.  **The Generator LLM:** Tasked solely with synthesizing the long-form report using a prompt and dynamically generated local Vector Database context. It is optimized for fluency.
2.  **The Evaluator LLM (The Judge):** A separate LLM instance equipped with specialized tools (like `VectorSearch`). It does not generate the report; it reads the draft sentence-by-sentence.
3.  **The Verification Loop:** For every factual claim in the draft, the Evaluator LLM formulates a query, uses the `VectorSearch` tool to retrieve the exact relevant chunk from the local Vector Database, and grades the claim against that chunk.
4.  **Feedback/Regeneration:** If the Evaluator assigns a low faithfulness score, it provides a tool-backed rationale. The orchestrator can then either prompt the Generator to fix the specific error or flag it in the UI for the human user.

**Why this works:** The Evaluator does not rely on its massive context window or parametric memory to spot errors. It uses the `VectorSearch` tool to look at tiny, highly relevant snippets of truth, dramatically reducing Evaluator hallucinations.

**Alternatives Considered & Rejected:**

- **LLM-as-a-Judge (No Tools):** We considered having a second LLM just read the draft and the full source document to spot errors. _Rejected_ because giving the Evaluator a 100k token source document leads to the "Lost in the Middle" problem; the Evaluator itself will hallucinate whether a fact exists.
- **Regex / Deterministic Citation Checking:** Appending `[citation x]` to every generated sentence and using regex to ensure the cited chunk supports the text via embeddings. _Rejected_ because embeddings measure semantic similarity, not logical entailment. A sentence stating the opposite of a source text often has a very high cosine similarity to it.
- **Multi-Agent Debate:** Having three LLMs argue about the truthfulness of a text. _Rejected_ due to prohibitive token costs for 20-page documents and latency issues.

**Production Realities:**

- **Cost:** This doubles the token cost. We mitigate this by using a smaller, cheaper, fast model (e.g., Llama 3 70B via Groq) for the Evaluator, as grading against a specific snippet requires less reasoning capability than synthesizing a 20-page report (which might use a heavier model like Gemini 1.5 Pro).
- **Latency:** The Evaluator can grade sections asynchronously as they stream from the Generator, hiding the latency from the user.

## 4. Validation Plan

Before scaling to 10,000 users, we must rigorously validate this architecture.

**First 2 Weeks of Testing:**

1.  **The "Needle in the Haystack" Sabotage (Days 1-5):** I would create a golden dataset of 50 perfect 10-page reports based on a standardized knowledge base. I would systematically inject 200 known hallucinations (changing numbers, flipping negatives/positives, attributing quotes to the wrong people).
2.  **Tool Efficacy Test (Days 6-10):** Run the Evaluator Agent on the sabotaged dataset. We test the `VectorSearch` tool specifically: Does the Evaluator formulate the correct search queries to find the contradiction? Does it successfully retrieve the chunk?
3.  **Human Alignment (Days 11-14):** Have domain experts review 100 flags raised by the Evaluator to measure the False Positive rate.

**Why test this first?** The entire architecture rests on the assumption that the Evaluator LLM can effectively use the `VectorSearch` tool to find the _absence_ of information or a specific contradiction. If the search tool returns poor chunks, the Evaluator is blind.

**Failure Scenarios:**

- **The Overzealous Grader:** If the Evaluator's False Positive rate exceeds 15% (flagging accurate summaries as hallucinations because they don't use the exact wording of the source), users will lose trust. We would need to relax the prompt or abandon this for a softer evaluation method.
- **Tool Dependency Bottleneck:** If the semantic search fails to retrieve relevant chunks because the Generator used different terminology than the source, the Evaluator will falsely flag extrinsic hallucinations.

**Iterations:**

- **v1 (Current):** Evaluator grades post-generation using simple vector search. Output is pass/fail.
- **v2:** Evaluator streams grading iteratively during generation.
- **v3:** Evaluator toolset expands to include `GraphSearch` for complex multi-hop logical verifications.

**Open Questions:**

- What is the optimal chunk size for the local Vector Database to ensure the Evaluator gets enough context to judge a claim without being overwhelmed?
- How do we prevent Evaluator "sycophancy," where an overly confident Generator tricks the Evaluator into agreeing with a hallucination?
