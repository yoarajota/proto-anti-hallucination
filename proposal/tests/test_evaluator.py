import sys
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure the src folder is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from evaluator_agent import EvaluatorAgent
from tool_registry import ToolRegistry

@pytest.fixture
def test_registry():
    os.environ["GROQ_API_KEY"] = "testsuite"
    registry = ToolRegistry(collection_name="test_db")
    registry.load_context(["Tommy Atkins accounts for 80% of Brazilian mango exports.", "The Palmer variety has virtually fiberless flesh."])
    return registry

@patch('evaluator_agent.AsyncGroq')
def test_evaluator_scores_hallucination(mock_groq, test_registry):
    mock_client = MagicMock()
    mock_acompletion = AsyncMock()
    mock_client.chat.completions.create = mock_acompletion
    mock_groq.return_value = mock_client
    
    # First response: LLM decides to call a tool
    mock_resp_1 = MagicMock()
    mock_msg_1 = mock_resp_1.choices[0].message
    mock_msg_1.content = None
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "vector_search"
    mock_tool_call.function.arguments = '{"query": "Tommy Atkins exports"}'
    mock_msg_1.tool_calls = [mock_tool_call]
    
    # Second response: LLM returns JSON evaluation
    mock_resp_2 = MagicMock()
    mock_msg_2 = mock_resp_2.choices[0].message
    mock_msg_2.content = '{"faithfulness_score": 0.0, "requires_revision": true, "rationale": "Contradicts Tommy Atkins export share"}'
    mock_msg_2.tool_calls = None
    
    mock_acompletion.side_effect = [mock_resp_1, mock_resp_2]

    agent = EvaluatorAgent(test_registry)
    result = asyncio.run(agent.evaluate_claim("Tommy Atkins accounts for 100% of Brazilian mango exports."))

    assert result['faithfulness_score'] == 0.0
    assert result['requires_revision'] is True

@patch('evaluator_agent.AsyncGroq')
def test_evaluator_scores_truth(mock_groq, test_registry):
    mock_client = MagicMock()
    mock_acompletion = AsyncMock()
    mock_client.chat.completions.create = mock_acompletion
    mock_groq.return_value = mock_client

    # First response: LLM decides to call a tool
    mock_resp_1 = MagicMock()
    mock_msg_1 = mock_resp_1.choices[0].message
    mock_msg_1.content = None
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_456"
    mock_tool_call.function.name = "vector_search"
    mock_tool_call.function.arguments = '{"query": "Tommy Atkins exports"}'
    mock_msg_1.tool_calls = [mock_tool_call]
    
    # Second response: LLM returns JSON evaluation
    mock_resp_2 = MagicMock()
    mock_msg_2 = mock_resp_2.choices[0].message
    mock_msg_2.content = '```json\n{"faithfulness_score": 1.0, "requires_revision": false, "rationale": "Perfect match"}\n```'
    mock_msg_2.tool_calls = None
    
    mock_acompletion.side_effect = [mock_resp_1, mock_resp_2]

    agent = EvaluatorAgent(test_registry)
    result = asyncio.run(agent.evaluate_claim("Tommy Atkins accounts for 80% of Brazilian mango exports."))

    assert result['faithfulness_score'] == 1.0
    assert result['requires_revision'] is False

