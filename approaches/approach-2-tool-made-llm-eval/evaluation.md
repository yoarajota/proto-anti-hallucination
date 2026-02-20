### Approach: Tool-Made LLM Eval

#### 1. Discovery & Definition

- **Core Concept**: This approach delegates the verification of generated text to a specialized evaluation LLM equipped with external assessment tools (e.g., Python execution environments, web search, or fact-checking APIs). Every execution begins by dynamically generating a knowledge base/context from an initial user prompt. A separate "Evaluator" agent then scans the primary generation against this context using its tools to identify hallucinations.
- **Mechanism**: It addresses **factuality** by actively looking up claims using external tools (like checking a calculator for math or a reliable database for metrics). It addresses **faithfulness** by having the evaluator mathematically or programmatically verify that the output faithfully represents the generated context, flagging unsupported entity additions.

#### 2. Trade-off Analysis

- **Pros**: Grounded verification. By relying on external tools rather than pure LLM reasoning, it significantly reduces the "hallucination cascade" where an evaluator hallucinatnes a verification. It's often more deterministic for quantifiable facts.
- **Cons**: High engineering overhead to maintain the tool registry. Latency is heavily dependent on the speed of external tools (e.g., waiting for web searches or API responses).
- **Resource Cost**: Medium to High. While the evaluator might use fewer tokens than a full debate, API calls to external tools can incur additional financial and rate-limiting costs across 10k users.
- **Latency Impact**: Moderate to High impact. Waiting for a Python script or an API to validate claims across a 20-page document introduces blocking steps. The latency can spike unpredictably based on third-party tool performance.

#### 3. Feasibility Check

- **Complexity**: Moderate. The challenge lies in creating robust tool interfaces and ensuring the evaluator knows exactly _when_ and _how_ to use them.
- **Critical Failure Modes**:
  - **Tool Failure/Timeout**: If the verification API goes down, the system might have to fail-open (allowing unverified text) or fail-closed (breaking the generation entirely). (Fails loudly).
  - **Tool Misuse**: The evaluator might use the wrong tool for a specific claim, leading to False Positives or False Negatives. (Fails silently).
- **Decision**: [x] Adopt / [ ] Reject
  - _Reasoning_: The deterministic nature of tool-use provides a much stronger capability for verifying 5-20 page documents than pure LLM debate. While latency and tool maintenance are concerns, they can be optimized through caching and asynchronous evaluation, making this the more scalable and reliable architecture for our target user base.
