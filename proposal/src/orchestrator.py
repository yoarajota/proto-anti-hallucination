import logging
import asyncio
from typing import List, Dict
from tool_registry import ToolRegistry
from evaluator_agent import EvaluatorAgent
from document_generator import DocumentGenerator

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, source_text_path: str, model: str = "llama-3.3-70b-versatile", num_sections: int = 5):
        """
        Initializes the Orchestrator by loading the ground truth document 
        and initializing the Evaluator Agent and Generator.
        """
        self.tool_registry = ToolRegistry()
        self.source_text_path = source_text_path
        
        # Load and chunk source text
        self.source_text = self._load_file(source_text_path)
        chunks = self._chunk_source_text(self.source_text)
        self.tool_registry.load_context(chunks)
        
        self.evaluator = EvaluatorAgent(self.tool_registry, model=model)
        self.generator = DocumentGenerator(model=model, num_sections=num_sections)
        
    def _load_file(self, filepath: str) -> str:
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return ""

    def _chunk_source_text(self, text: str) -> List[str]:
        """Simple paragraph-based chunking strategy for the vector DB context."""
        return [c.strip() for c in text.split('\n\n') if c.strip()]

    def _robust_sentence_chunking(self, text: str, window_size: int = 2) -> List[str]:
        """
        Splits text into sliding window chunks of sentences to preserve context for the evaluator.
        """
        raw_sentences = [s.strip() + "." for s in text.replace('\n', ' ').split('. ') if len(s.strip()) > 20]
        chunks = []
        for i in range(len(raw_sentences)):
            start = max(0, i - window_size + 1)
            chunk = " ".join(raw_sentences[start:i+1])
            chunks.append(chunk)
        return chunks

    async def evaluate_claims_concurrently(self, claims: List[str], max_concurrency: int = 50) -> List[Dict]:
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def sem_evaluate(claim):
            async with semaphore:
                verdict = await self.evaluator.evaluate_claim(claim)
                return {"claim": claim, "verdict": verdict}

        tasks = [asyncio.create_task(sem_evaluate(claim)) for claim in claims]
        logger.info(f"Evaluating {len(claims)} claims concurrently...")
        return await asyncio.gather(*tasks)

    async def generate_and_evaluate_pipeline(self, user_prompt: str, output_path: str, print_stream: bool = False) -> List[Dict]:
        """
        The full end-to-end pipeline:
        1. Generate a draft report based on the source text asynchronously (streaming).
        2. Buffer sentences from the stream and evaluate them in real-time.
        3. Save the draft to disk.
        """
        logger.info("Starting Generation and Real-time Evaluation Phase...")
        
        generated_draft_parts = []
        evaluation_tasks = []
        buffer = ""
        
        semaphore = asyncio.Semaphore(50)
        
        async def evaluate_and_store_buffer(text_chunk):
            async with semaphore:
                verdict = await self.evaluator.evaluate_claim(text_chunk)
                return {"claim": text_chunk, "verdict": verdict}

        async for chunk in self.generator.generate_report_stream(self.source_text, user_prompt):
            if print_stream:
                print(chunk, end="", flush=True)
            generated_draft_parts.append(chunk)
            buffer += chunk
            
            # Simple sentence boundary detection for real-time dispatch
            if '. ' in buffer or '.\n' in buffer:
                # We have at least one complete sentence
                parts = buffer.split('. ', 1)
                if len(parts) > 1:
                    complete_sentence = parts[0].strip() + "."
                    buffer = parts[1]
                    
                    if len(complete_sentence) > 20: 
                        # Use complete sentence for evaluation
                        task = asyncio.create_task(evaluate_and_store_buffer(complete_sentence))
                        evaluation_tasks.append(task)
                        
        # Flush remaining buffer
        if len(buffer.strip()) > 20:
            task = asyncio.create_task(evaluate_and_store_buffer(buffer.strip()))
            evaluation_tasks.append(task)
            
        final_draft = "".join(generated_draft_parts)
        
        with open(output_path, 'w') as f:
            f.write(final_draft)
        logger.info(f"Draft report saved to {output_path}")
        
        logger.info(f"Waiting for {len(evaluation_tasks)} remaining evaluation tasks to complete...")
        if evaluation_tasks:
            results = await asyncio.gather(*evaluation_tasks)
        else:
            results = []
            
        return results

    async def evaluate_document(self, generated_text_path: str) -> List[Dict]:
        """
        Reads a generated report, breaks it down into robust chunks,
        and sends them to the EvaluatorAgent for strictly verified scoring asynchronously.
        """
        generated_text = self._load_file(generated_text_path)
        if not generated_text:
            return []

        claims = self._robust_sentence_chunking(generated_text)
        return await self.evaluate_claims_concurrently(claims)
