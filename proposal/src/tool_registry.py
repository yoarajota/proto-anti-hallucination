import json
import chromadb
from typing import List

class ToolRegistry:
    def __init__(self, collection_name: str = "source_knowledge"):
        self.chroma_client = chromadb.Client()
        # In-memory ephemeral DB by default
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)
        
        # Define the tools available to the Evaluator LLM
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "vector_search",
                    "description": "Searches the factual local knowledge base for a specific query to verify a claim.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The specific factual question or keywords to search for."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def load_context(self, text_chunks: List[str]):
        """Loads factual context into the Vector Database."""
        if not text_chunks:
            return
            
        # Optional: chunking could happen here. We assume chunks are pre-split.
        ids = [str(i) for i in range(len(text_chunks))]
        self.collection.add(
            documents=text_chunks,
            ids=ids
        )

    def vector_search(self, query: str) -> str:
        """Executes a semantic search against the loaded context."""
        results = self.collection.query(
            query_texts=[query],
            n_results=2
        )
        
        if results and results.get('documents') and len(results['documents'][0]) > 0:
            # Return the top matches as a single string
            return "\n".join(results['documents'][0])
        
        return "No relevant information found in the source documents."

    def evaluate_claim_by_vector(self, claim: str) -> dict:
        """Evaluates a claim directly using vector distance from the knowledge base."""
        results = self.collection.query(
            query_texts=[claim],
            n_results=1,
            include=["documents", "distances"]
        )
        
        if not results or not results.get('documents') or not results['documents'][0]:
            return {
                "faithfulness_score": 0.0,
                "requires_revision": True,
                "rationale": "No context found in vector knowledge base."
            }
            
        distance = results['distances'][0][0]
        match_text = results['documents'][0][0]
        
        # Map L2 distance to a score. 
        # Lower distance = more faithful.
        score = max(0.0, 1.0 - (distance / 1.5)) 
        score = min(1.0, score)
        
        requires_revision = score < 0.8
        
        return {
            "faithfulness_score": round(score, 2),
            "requires_revision": requires_revision,
            "rationale": f"Vector distance: {distance:.3f}. Closest match: '{match_text}'"
        }
        
    def execute_tool(self, tool_name: str, kwargs: dict) -> str:
        """Route tool execution from LLM to appropriate function."""
        if tool_name == "vector_search":
            return self.vector_search(**kwargs)
        raise ValueError(f"Unknown tool requested by LLM: {tool_name}")
