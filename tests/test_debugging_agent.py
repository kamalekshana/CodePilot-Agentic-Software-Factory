
import json

from agents.debugging_agent import DebuggingAgent
from schemas.agent_response import AgentStatus


class FakeLLMClient:
    def __init__(self, response):
        self.response = response

    def generate_response(self, system_prompt, user_prompt):
        return self.response


def test_debugging_agent_creates_fix_task():
    response = {
        "filename": "inventory.py",
        "error_summary": "Stock quantity is not updated.",
        "root_cause": "The update function does not save the new quantity.",
        "correction_instructions": "Update the stock quantity and persist it.",
        "related_test": "test_stock_update",
        "priority": "high",
    }

    agent = DebuggingAgent(
        FakeLLMClient(json.dumps(response))
    )

    result = agent.create_fix_task(
        filename="inventory.py",
        source_code="def update_stock(): pass",
        test_report="1 failed: test_stock_update",
    )

    assert result.status == AgentStatus.SUCCESS
    assert result.metadata["fix_task"]["filename"] == "inventory.py"
    assert result.metadata["analysis_completed"] is True


def test_debugging_agent_rejects_invalid_json():
    agent = DebuggingAgent(
        FakeLLMClient("This is not JSON")
    )

    result = agent.create_fix_task(
        filename="inventory.py",
        source_code="def update_stock(): pass",
        test_report="1 failed",
    )

    assert result.status == AgentStatus.FAILED
    assert result.error is not None


def test_debugging_agent_requires_filename():
    agent = DebuggingAgent(
        FakeLLMClient("{}")
    )

    result = agent.create_fix_task(
        filename="",
        source_code="print('hello')",
        test_report="1 failed",
    )

    assert result.status == AgentStatus.FAILED
