import json

import pytest

from services.planning_workflow import PlanningWorkflow


class FakeRequirementsAgent:
    def analyze_requirements(self, user_request):
        return f"# Requirements\n\nRequest: {user_request}"


class FakeArchitectAgent:
    def generate_architecture(self, requirements):
        assert "Requirements" in requirements
        return "# Architecture\n\nThree-layer architecture."

    def generate_database_design(self, requirements):
        assert "Requirements" in requirements
        return "# Database Design\n\nProject entity."


class FakePlannerAgent:
    def generate_plan(self, requirements, architecture):
        assert "Requirements" in requirements
        assert "Architecture" in architecture
        return {
            "tasks": [{"task_id": "TASK-001", "title": "Build MVP"}],
            "execution_order": ["TASK-001"],
        }


def create_workflow(tmp_path):
    return PlanningWorkflow(
        requirements_agent=FakeRequirementsAgent(),
        architect_agent=FakeArchitectAgent(),
        planner_agent=FakePlannerAgent(),
        workspace_dir=tmp_path,
    )


def test_complete_pipeline_generates_four_artifacts(tmp_path):
    workflow = create_workflow(tmp_path)

    result = workflow.run(
        project_name="Demo Project",
        user_request="Build a task management application.",
    )

    artifacts = result["artifacts"]

    assert len(artifacts) == 4
    assert all(path for path in artifacts.values())

    for path in artifacts.values():
        assert __import__("pathlib").Path(path).exists()


def test_pipeline_passes_outputs_between_agents(tmp_path):
    workflow = create_workflow(tmp_path)

    result = workflow.run(
        project_name="Integration Test",
        user_request="Build an inventory application.",
    )

    assert "inventory application" in result["requirements"]
    assert "Architecture" in result["architecture"]
    assert "Database Design" in result["database_design"]


def test_implementation_plan_is_saved_as_valid_json(tmp_path):
    workflow = create_workflow(tmp_path)

    result = workflow.run(
        project_name="JSON Test",
        user_request="Build a booking application.",
    )

    plan_path = result["artifacts"]["implementation_plan"]
    saved_plan = json.loads(
        __import__("pathlib").Path(plan_path).read_text(encoding="utf-8")
    )

    assert saved_plan == result["implementation_plan"]
    assert saved_plan["execution_order"] == ["TASK-001"]


@pytest.mark.parametrize(
    "project_name,user_request",
    [
        ("", "Build an application."),
        ("Demo", ""),
        ("   ", "Build an application."),
        ("Demo", "   "),
    ],
)
def test_pipeline_rejects_empty_inputs(
    tmp_path, project_name, user_request
):
    workflow = create_workflow(tmp_path)

    with pytest.raises(ValueError):
        workflow.run(project_name, user_request)


def test_pipeline_rejects_empty_agent_output(tmp_path):
    workflow = create_workflow(tmp_path)
    workflow.requirements_agent.analyze_requirements = lambda request: ""

    with pytest.raises(ValueError, match="Requirements Agent"):
        workflow.run("Demo", "Build an application.")
