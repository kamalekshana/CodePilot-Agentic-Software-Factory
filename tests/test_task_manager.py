
import pytest

from core.task_manager import TaskManager
from schemas.task import TaskStatus


def create_manager():
    return TaskManager()


def test_create_task():
    manager = create_manager()

    task = manager.create_task(
        agent_name="Requirements Agent",
        description="Analyze requirements",
        input_data="Build a calculator",
    )

    assert task.task_id == "TASK-001"
    assert task.agent_name == "Requirements Agent"
    assert task.status == TaskStatus.PENDING


def test_create_task_with_dependency():
    manager = create_manager()

    first = manager.create_task(
        agent_name="Requirements Agent",
        description="Analyze requirements",
    )

    second = manager.create_task(
        agent_name="Architect Agent",
        description="Design architecture",
        depends_on=[first.task_id],
    )

    assert second.depends_on == [first.task_id]


def test_reject_unknown_dependency():
    manager = create_manager()

    with pytest.raises(ValueError, match="Dependency task not found"):
        manager.create_task(
            agent_name="Architect Agent",
            description="Design architecture",
            depends_on=["TASK-999"],
        )


def test_reject_empty_agent_name():
    manager = create_manager()

    with pytest.raises(ValueError):
        manager.create_task("", "Analyze requirements")


def test_update_task_status_and_output():
    manager = create_manager()

    task = manager.create_task(
        agent_name="Coding Agent",
        description="Generate code",
    )

    manager.update_status(task.task_id, TaskStatus.IN_PROGRESS)
    assert task.started_at is not None

    manager.set_output(task.task_id, "print('Hello')")

    manager.update_status(task.task_id, TaskStatus.COMPLETED)

    assert task.status == TaskStatus.COMPLETED
    assert task.output_data == "print('Hello')"
    assert task.completed_at is not None


def test_get_task_rejects_unknown_id():
    manager = create_manager()

    with pytest.raises(KeyError):
        manager.get_task("TASK-999")


def test_get_tasks_by_status():
    manager = create_manager()

    first = manager.create_task("Agent A", "Task A")
    second = manager.create_task("Agent B", "Task B")

    manager.update_status(first.task_id, TaskStatus.COMPLETED)

    completed = manager.get_tasks_by_status(TaskStatus.COMPLETED)
    pending = manager.get_tasks_by_status(TaskStatus.PENDING)

    assert len(completed) == 1
    assert completed[0].task_id == first.task_id
    assert len(pending) == 1
    assert pending[0].task_id == second.task_id
