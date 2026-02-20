import os
import json
import logging
import asyncio
from dotenv import load_dotenv
from orchestrator import Orchestrator

load_dotenv()

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    model_name = "llama-3.3-70b-versatile" 

    # Initialize Orchestrator and load our ground-truth vector DB
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_dir = os.path.join(script_dir, "..", "scenario")
    
    source_file = os.path.join(scenario_dir, "source_knowledge.txt")
    orchestrator = Orchestrator(source_text_path=source_file, model=model_name, num_sections=5)
    print("Context loaded successfully into ChromaDB!")

    generated_file = os.path.join(scenario_dir, "mocked_generation.md")
    print(f"Beginning statement-by-statement evaluation of {generated_file}...")

    results = await orchestrator.evaluate_document(generated_file)

    for idx, r in enumerate(results):
        claim = r['claim']
        verdict = r['verdict']
        
        # We highlight failures
        if verdict.get('requires_revision', True) or verdict.get('faithfulness_score', 0) < 0.8:
            print(f"\n🚨 [HALLUCINATION DETECTED] \nClaim: {claim}")
            print(f"Score: {verdict.get('faithfulness_score')}")
            print(f"Rationale: {verdict.get('rationale')}")
            print("-" * 50)

    # We will ask the Generator to write a summary, saving it to a new file, and then evaluate it.
    user_prompt = "Tell me about the history of the Apollo 11 moon landing."
    output_file = os.path.join(scenario_dir, "dynamic_generation.md")

    print(f"\nUser provides the topic: '{user_prompt}'")
    print("System will OVERRIDE this and force a 5-20 page generation about Brazilian Mangos (Prototype constraint).")

    print("\n1. Generating new draft...")
    dynamic_results = await orchestrator.generate_and_evaluate_pipeline(user_prompt, output_file)

    print("\n2. Evaluation Complete! Let's see if the generator hallucinated anything this time:")
    for idx, r in enumerate(dynamic_results):
        verdict = r['verdict']
        if verdict.get('requires_revision', True):
            print(f"🚨 Hallucination found in dynamic generation: {r['claim']}")
        else:
            print(f"✅ Verified Fact: {r['claim']}")

if __name__ == "__main__":
    asyncio.run(main())
