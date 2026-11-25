
import json

import pytest

from agents.planner_agent import PlannerAgent


VALID_PLAN = {
    "project_name": "Pharmacy Inventory System",
    "summary": "Implementation plan for a pharmacy inventory application.",
    "tasks": [
        {
            "task_id": "TASK-001",
            "title": "Set up project",
            "description": "Create the initial project structure.",
            "priority": "high",
            "dependencies": [],
            "completion_criteria": ["Project structure is created."],
        },
        {
            "task_id": "TASK-002",
            "title": "Implement inventory",
            "description": "Implement inventory tracking.",
            "priority": "high",
            "dependencies": ["TASK-001"],
            "completion_criteria": ["Inventory tracking works."],
        },
        {
            "task_id": "TASK-003",
            "title": "Test inventory",
            "description": "Test inventory functionality.",
            "priority": "medium",
            "dependencies": ["TASK-002"],
            "completion_criteria": ["Inventory tests pass."],
        },
    ],
    "execution_order": ["TASK-001", "TASK-002", "TASK-003"],
}


class MockLLMClient:
    def __init__(self, response=None):
        self.response = (
            json.dumps(VALID_PLAN)
            if response is None
            else response
        )
        self.prompts = []

    def generate_response(self, system_prompt, user_prompt, **kwargs):
        self.prompts.append((system_prompt, user_prompt))
        return self.response


def create_agent(response=None):
    mock = MockLLMClient(response)
    agent = PlannerAgent(llm_client=mock)
    return agent, mock


def test_planner_initialization():
    agent, _ = create_agent()

    assert agent.name == "Planner Agent"
    assert agent.role == "Software Implementation Planning"


def test_planner_system_prompt():
    agent, _ = create_agent()

    assert "valid JSON" in agent.system_prompt
    assert "dependencies" in agent.system_prompt


def test_generate_valid_plan():
    agent, mock = create_agent()

    result = agent.generate_plan(
        "Pharmacy inventory requirements",
        "Layered application architecture",
    )

    assert result["project_name"] == "Pharmacy Inventory System"
    assert len(result["tasks"]) == 3
    assert result["execution_order"] == [
        "TASK-001",
        "TASK-002",
        "TASK-003",
    ]
    assert "Pharmacy inventory requirements" in mock.prompts[0][1]
    assert "Layered application architecture" in mock.prompts[0][1]


def test_generate_plan_from_markdown_fenced_json():
    fenced_response = (
        "```json\n"
        + json.dumps(VALID_PLAN)
        + "\n```"
    )

    agent, _ = create_agent(fenced_response)

    result = agent.generate_plan("Requirements", "Architecture")

    assert result["project_name"] == "Pharmacy Inventory System"


def test_reject_empty_requirements():
    agent, _ = create_agent()

    with pytest.raises(ValueError, match="Requirements"):
        agent.generate_plan("", "Architecture")


def test_reject_empty_architecture():
    agent, _ = create_agent()

    with pytest.raises(ValueError, match="Architecture"):
        agent.generate_plan("Requirements", "  ")


def test_reject_invalid_json():
    agent, _ = create_agent("This is not valid JSON")

    with pytest.raises(RuntimeError, match="invalid JSON"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_duplicate_task_ids():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["tasks"][1]["task_id"] = "TASK-001"

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="Duplicate task IDs"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_unknown_dependency():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["tasks"][1]["dependencies"] = ["TASK-999"]

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="Unknown dependency"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_circular_dependencies():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["tasks"][0]["dependencies"] = ["TASK-003"]

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="Circular dependency"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_incorrect_execution_order():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["execution_order"] = [
        "TASK-002",
        "TASK-001",
        "TASK-003",
    ]

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="must appear before"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_missing_completion_criteria():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["tasks"][0]["completion_criteria"] = []

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="completion_criteria"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_missing_execution_task():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["execution_order"] = ["TASK-001", "TASK-002"]

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="every task ID"):
        agent.generate_plan("Requirements", "Architecture")


def test_reject_unexpected_fields():
    invalid_plan = json.loads(json.dumps(VALID_PLAN))
    invalid_plan["unexpected_field"] = "not allowed"

    agent, _ = create_agent(json.dumps(invalid_plan))

    with pytest.raises(RuntimeError, match="invalid implementation plan"):
        agent.generate_plan("Requirements", "Architecture")
