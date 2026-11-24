
from datetime import datetime, timezone

from schemas.workflow import Workflow, WorkflowStatus


class StateManager:
    """Manages workflow states and execution progress."""

    def __init__(self):
        self.workflows: dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> Workflow:
        """Register a new workflow."""

        if workflow.workflow_id in self.workflows:
            raise ValueError(
                f"Workflow already exists: {workflow.workflow_id}"
            )

        self.workflows[workflow.workflow_id] = workflow

        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow:
        """Retrieve a workflow using its ID."""

        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise KeyError(f"Workflow not found: {workflow_id}")

        return workflow

    def update_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        error: str | None = None,
    ) -> Workflow:
        """Update workflow status and timestamps."""

        workflow = self.get_workflow(workflow_id)
        now = datetime.now(timezone.utc)

        if status == WorkflowStatus.IN_PROGRESS:
            if workflow.started_at is None:
                workflow.started_at = now

        if status in (
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
        ):
            workflow.completed_at = now

        workflow.status = status
        workflow.error = error

        return workflow

    def set_current_task(
        self,
        workflow_id: str,
        task_id: str | None,
    ) -> Workflow:
        """Update the currently executing task."""

        workflow = self.get_workflow(workflow_id)

        if task_id is not None:
            task_ids = {task.task_id for task in workflow.tasks}

            if task_id not in task_ids:
                raise ValueError(
                    f"Task {task_id} does not belong to workflow "
                    f"{workflow_id}"
                )

        workflow.current_task_id = task_id

        return workflow

    def add_task(self, workflow_id: str, task) -> Workflow:
        """Add a task to an existing workflow."""

        workflow = self.get_workflow(workflow_id)

        if any(
            existing.task_id == task.task_id
            for existing in workflow.tasks
        ):
            raise ValueError(
                f"Task already exists in workflow: {task.task_id}"
            )

        workflow.tasks.append(task)

        return workflow

    def save_final_output(
        self,
        workflow_id: str,
        output: str,
    ) -> Workflow:
        """Store the final workflow output."""

        workflow = self.get_workflow(workflow_id)
        workflow.final_output = output

        return workflow

    def get_all_workflows(self) -> list[Workflow]:
        """Return all registered workflows."""

        return list(self.workflows.values())
