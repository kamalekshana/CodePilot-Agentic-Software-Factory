
from core.state_manager import StateManager
from core.task_manager import TaskManager
from schemas.task import TaskStatus
from schemas.workflow import Workflow, WorkflowStatus


class Orchestrator:
    """
    Central controller responsible for coordinating
    specialized agents and executing workflows sequentially.
    """

    def __init__(
        self,
        agents: dict,
        task_manager: TaskManager | None = None,
        state_manager: StateManager | None = None,
    ):
        if not agents:
            raise ValueError("At least one agent must be registered.")

        self.agents = agents
        self.task_manager = task_manager or TaskManager()
        self.state_manager = state_manager or StateManager()
        self._workflow_counter = 0

    def run_workflow(
        self,
        project_name: str,
        user_request: str,
        agent_names: list[str],
    ) -> Workflow:
        """Create and execute a sequential multi-agent workflow."""

        if not project_name.strip():
            raise ValueError("Project name cannot be empty.")

        if not user_request.strip():
            raise ValueError("User request cannot be empty.")

        if not agent_names:
            raise ValueError("At least one agent is required.")

        for agent_name in agent_names:
            if agent_name not in self.agents:
                raise ValueError(
                    f"Agent is not registered: {agent_name}"
                )

        self._workflow_counter += 1
        workflow_id = f"WF-{self._workflow_counter:03d}"

        workflow = Workflow(
            workflow_id=workflow_id,
            project_name=project_name,
            user_request=user_request,
        )

        self.state_manager.register_workflow(workflow)

        try:
            self.state_manager.update_status(
                workflow_id,
                WorkflowStatus.IN_PROGRESS,
            )

            # Create all tasks before beginning execution.
            previous_task_id = None

            for agent_name in agent_names:
                agent = self.agents[agent_name]

                task = self.task_manager.create_task(
                    agent_name=agent_name,
                    description=(
                        f"{agent.role} task for project: {project_name}"
                    ),
                    input_data=user_request,
                    depends_on=(
                        [previous_task_id]
                        if previous_task_id
                        else []
                    ),
                )

                self.state_manager.add_task(workflow_id, task)
                previous_task_id = task.task_id

            previous_output = user_request
            final_output = ""

            # Execute tasks sequentially.
            for index, task in enumerate(workflow.tasks):
                self.state_manager.set_current_task(
                    workflow_id,
                    task.task_id,
                )

                task.input_data = previous_output

                self.task_manager.update_status(
                    task.task_id,
                    TaskStatus.IN_PROGRESS,
                )

                agent = self.agents[task.agent_name]
                response = agent.execute(task.input_data)

                if response.status.value != "success":
                    error_message = (
                        response.error or "Agent execution failed."
                    )

                    self.task_manager.update_status(
                        task.task_id,
                        TaskStatus.FAILED,
                        error=error_message,
                    )

                    # Tasks after the failed task cannot execute.
                    for remaining_task in workflow.tasks[index + 1:]:
                        self.task_manager.update_status(
                            remaining_task.task_id,
                            TaskStatus.BLOCKED,
                            error="Blocked because a previous task failed.",
                        )

                    self.state_manager.update_status(
                        workflow_id,
                        WorkflowStatus.FAILED,
                        error=error_message,
                    )

                    self.state_manager.set_current_task(
                        workflow_id,
                        None,
                    )

                    return workflow

                self.task_manager.set_output(
                    task.task_id,
                    response.output,
                )

                self.task_manager.update_status(
                    task.task_id,
                    TaskStatus.COMPLETED,
                )

                previous_output = response.output
                final_output = response.output

            self.state_manager.save_final_output(
                workflow_id,
                final_output,
            )

            self.state_manager.update_status(
                workflow_id,
                WorkflowStatus.COMPLETED,
            )

            self.state_manager.set_current_task(
                workflow_id,
                None,
            )

            return workflow

        except Exception as error:
            self.state_manager.update_status(
                workflow_id,
                WorkflowStatus.FAILED,
                error=f"{type(error).__name__}: {error}",
            )

            self.state_manager.set_current_task(
                workflow_id,
                None,
            )

            raise
