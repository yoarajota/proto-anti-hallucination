# Reliable AI Writing Systems Challenge - Action Plan

This plan is divided into "General Steps" (shared across the entire project) and "Approach-Scoped Steps" (a template to be repeated for each specific solution you investigate).

## 🟢 General Steps (Shared)

These steps provide the foundation and the final deliverables. They are independent of the specific technical approach you choose.

### Phase 1: Problem Space Analysis

- [ ] **Decompose the Problem**
  - [ ] Map specific hallucination types (Faithfulness vs. Factuality) to the long-form context.
  - [ ] Identify root causes relevant to 5-20 page documents (Context Window limits, "Lost in the Middle").
  - [ ] Differentiate between "symptoms" (wrong number) and "disease" (tokenizer issue vs. logic gap).
- [ ] **Define Constraints & Requirements**
  - [ ] Analyze the user base (10k users, research/technical domain).
  - [ ] distinct failure modes for this demographic (e.g., a subtle logical error is worse than a blatant crash).

### Phase 2: Success Metrics (The Rubric)

- [ ] **Define "Success"**
  - [ ] Establish what constitutes a "tolerable" hallucination rate for this specific use case.
- [ ] **Design the Evaluation Rubric**
  - [ ] Define metrics for Precision (avoiding false positives) vs. Recall (catching all hallucinations).
  - [ ] Define the "Ground Truth" baseline (How do we know what is true?).
  - [ ] Determine the cost/latency budget for detection.

### Phase 3: Final Polish & Delivery

- [ ] **Proposal Assembly**
  - [ ] Write Section 1: Problem Decomposition.
  - [ ] Write Section 2: Evaluation Rubric.
  - [ ] Write Section 3: Proposed Architecture (incorporating the best approach).
  - [ ] Write Section 4: Validation Plan.
- [ ] **Video Presentation**
  - [ ] Draft script/outline (Key insight, Rubric defense, Architecture trade-off).
  - [ ] Record Loom Video (5-8 mins).
- [ ] **Submission**
  - [ ] Package PDF/Markdown + Video Link.
  - [ ] Send via email.

---

## 🔵 Approach-Scoped Steps (Template)

_Copy and paste this section for each new approach you investigate (e.g., RAG, Chain of Verification, Multi-Agent Debate)._

### Approach: [Name of Approach]

#### 1. Discovery & Definition

- [ ] **Core Concept**: Briefly describe how this approach works.
  - _Note: Every approach must start with dynamically generating the knowledge base/context from an initial user prompt (one-shot context)._
- [ ] **Mechanism**: How does it specifically address the defined hallucination types?
  - _Example: Does it fix "faithfulness" by grounding in the dynamically generated source text?_

#### 2. Trade-off Analysis

- [ ] **Pros**: What are the main advantages? (High accuracy? Low latency?)
- [ ] **Cons**: What are the main drawbacks? (Expensive? Slow? Complex?)
- [ ] **Resource Cost**: Estimate computational/financial cost at scale (10k users).
- [ ] **Latency Impact**: Will it slow down the 20-page document generation?

#### 3. Feasibility Check

- [ ] **Complexity**: Can this be realistically built/maintained?
- [ ] **Critical Failure Modes**: How does it fail? (Does it fail silently or loudly?)
- [ ] **Decision**: [ ] Adopt / [ ] Reject (and why).
