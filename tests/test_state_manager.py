
import pytest

from core.state_manager import StateManager
from schemas.task import Task
from schemas.workflow import Workflow, WorkflowStatus


def create_workflow(workflow_id="WF-001"):
    return Workflow(
        workflow_id=workflow_id,
        project_name="Calculator",
        user_request="Build a calculator application",
    )


def test_register_workflow():
    manager = StateManager()
    workflow = create_workflow()

    registered = manager.register_workflow(workflow)

    assert registered.workflow_id == "WF-001"
    assert manager.get_workflow("WF-001") == workflow


def test_reject_duplicate_workflow():
    manager = StateManager()
    workflow = create_workflow()

    manager.register_workflow(workflow)

    with pytest.raises(ValueError, match="already exists"):
        manager.register_workflow(workflow)


def test_get_unknown_workflow():
    manager = StateManager()

    with pytest.raises(KeyError):
        manager.get_workflow("WF-999")


def test_update_workflow_status():
    manager = StateManager()
    workflow = manager.register_workflow(create_workflow())

    manager.update_status("WF-001", WorkflowStatus.IN_PROGRESS)

    assert workflow.status == WorkflowStatus.IN_PROGRESS
    assert workflow.started_at is not None

    manager.update_status("WF-001", WorkflowStatus.COMPLETED)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert workflow.completed_at is not None


def test_add_task_to_workflow():
    manager = StateManager()
    workflow = manager.register_workflow(create_workflow())

    task = Task(
        task_id="TASK-001",
        agent_name="Requirements Agent",
        description="Analyze requirements",
    )

    manager.add_task("WF-001", task)

    assert len(workflow.tasks) == 1
    assert workflow.tasks[0].task_id == "TASK-001"


def test_reject_duplicate_task():
    manager = StateManager()
    manager.register_workflow(create_workflow())

    task = Task(
        task_id="TASK-001",
        agent_name="Requirements Agent",
        description="Analyze requirements",
    )

    manager.add_task("WF-001", task)

    with pytest.raises(ValueError, match="already exists"):
        manager.add_task("WF-001", task)


def test_set_current_task():
    manager = StateManager()
    workflow = manager.register_workflow(create_workflow())

    task = Task(
        task_id="TASK-001",
        agent_name="Requirements Agent",
        description="Analyze requirements",
    )

    manager.add_task("WF-001", task)
    manager.set_current_task("WF-001", "TASK-001")

    assert workflow.current_task_id == "TASK-001"

    manager.set_current_task("WF-001", None)

    assert workflow.current_task_id is None


def test_reject_task_not_belonging_to_workflow():
    manager = StateManager()
    manager.register_workflow(create_workflow())

    with pytest.raises(ValueError, match="does not belong"):
        manager.set_current_task("WF-001", "TASK-999")


def test_save_final_output():
    manager = StateManager()
    workflow = manager.register_workflow(create_workflow())

    manager.save_final_output("WF-001", "Calculator generated successfully.")

    assert workflow.final_output == "Calculator generated successfully."
