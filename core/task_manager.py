
from datetime import datetime, timezone

from schemas.task import Task, TaskStatus


class TaskManager:
    """Creates and manages tasks within CodePilot workflows."""

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self._task_counter = 0

    def create_task(
        self,
        agent_name: str,
        description: str,
        input_data: str = "",
        depends_on: list[str] | None = None,
    ) -> Task:
        """Create a new task and assign a unique ID."""

        if not agent_name.strip():
            raise ValueError("Agent name cannot be empty.")

        if not description.strip():
            raise ValueError("Task description cannot be empty.")

        dependencies = depends_on or []

        for dependency_id in dependencies:
            if dependency_id not in self.tasks:
                raise ValueError(
                    f"Dependency task not found: {dependency_id}"
                )

        self._task_counter += 1
        task_id = f"TASK-{self._task_counter:03d}"

        task = Task(
            task_id=task_id,
            agent_name=agent_name,
            description=description,
            input_data=input_data,
            depends_on=dependencies,
        )

        self.tasks[task_id] = task

        return task

    def get_task(self, task_id: str) -> Task:
        """Retrieve a task using its ID."""

        task = self.tasks.get(task_id)

        if task is None:
            raise KeyError(f"Task not found: {task_id}")

        return task

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        error: str | None = None,
    ) -> Task:
        """Update task status and relevant timestamps."""

        task = self.get_task(task_id)
        now = datetime.now(timezone.utc)

        if status == TaskStatus.IN_PROGRESS:
            if task.started_at is None:
                task.started_at = now

        if status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED,
        ):
            task.completed_at = now

        task.status = status
        task.error = error

        return task

    def set_output(self, task_id: str, output: str) -> Task:
        """Store the output produced by an agent."""

        task = self.get_task(task_id)
        task.output_data = output

        return task

    def get_all_tasks(self) -> list[Task]:
        """Return all registered tasks."""

        return list(self.tasks.values())

    def get_tasks_by_status(
        self,
        status: TaskStatus,
    ) -> list[Task]:
        """Return tasks matching a particular status."""

        return [
            task
            for task in self.tasks.values()
            if task.status == status
        ]
