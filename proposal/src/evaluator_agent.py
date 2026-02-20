import logging
import json
import asyncio
import re
from groq import AsyncGroq
from tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    def __init__(self, tool_registry: ToolRegistry, model: str = "llama-3.3-70b-versatile"):
        self.tool_registry = tool_registry
        self.model = model
        self.client = AsyncGroq()

    async def evaluate_claim(self, claim: str) -> dict:
        """
        Takes a single claim, asks the LLM to use the vector_search tool to find evidence,
        and uses the result to evaluate its faithfulness to avoid hallucinations.
        """
        logger.debug(f"Evaluating claim via LLM Eval with Tools: {claim}")
        
        system_prompt = """You are an Evaluator Agent. Your task is to check if a claim is factually grounded in the source context.
First, if you don't have the context yet, you MUST use the `vector_search` tool to search the local knowledge base for information related to the claim.
Once you have the context, you must evaluate the claim based ONLY on the source context. Do not use external knowledge.

When evaluating, return a JSON object with:
- faithfulness_score (float between 0.0 and 1.0)
- requires_revision (boolean)
- rationale (string explaining your decision)

A score of 1.0 means perfectly faithful to the source. 0.0 means completely unsupported or hallucinated."""

        max_retries = 5
        base_delay = 2

        for attempt in range(max_retries):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Claim payload: {claim}"}
            ]
            
            try:
                # Step 1: LLM decides to use tool or answer (should use tool)
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_registry.tools,
                    tool_choice="auto"
                )
                
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                
                if tool_calls:
                    # Step 2: Execute tool and return result to LLM
                    messages.append(response_message) # Add assistant's tool call message
                    
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        logger.debug(f"LLM called tool: {function_name} with args: {function_args}")
                        
                        try:
                            function_response = self.tool_registry.execute_tool(function_name, function_args)
                        except Exception as e:
                            logger.error(f"Error executing tool {function_name}: {e}")
                            function_response = f"Error: {e}"
                            
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": function_response,
                            }
                        )
                    
                    # Step 3: LLM evaluates with the context, forcing JSON format
                    messages.append({
                        "role": "system", 
                        "content": "Now use the tool results to output the evaluation JSON object as previously instructed. Ensure the output is valid JSON."
                    })
                    
                    second_response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        response_format={ "type": "json_object" }
                    )
                    
                    content = second_response.choices[0].message.content or "{}"
                else:
                    # The LLM decided not to use a tool (unexpected, but handle it)
                    logger.warning("LLM didn't use a tool, attempting to parse response directly.")
                    # the first response isn't guaranteed to be json, but we try
                    content = response_message.content or "{}"

                # Extract JSON cleanly
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    return json.loads(content[start:end+1])
                    
                return {
                    "faithfulness_score": 0.0,
                    "requires_revision": True,
                    "rationale": "Failed to parse LLM evaluation JSON."
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate limit" in error_str:
                    if attempt < max_retries - 1:
                        match = re.search(r'try again in ([0-9.]+)s', error_str)
                        delay = float(match.group(1)) + 1.0 if match else base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit reached. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(delay)
                        continue
                
                logger.error(f"LLM Eval Error: {e}")
                return {
                    "faithfulness_score": 0.0,
                    "requires_revision": True,
                    "rationale": f"LLM error: {e}"
                }
