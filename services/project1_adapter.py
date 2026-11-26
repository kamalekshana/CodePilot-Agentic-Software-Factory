
import importlib.util
import sys
import threading
from pathlib import Path
from types import ModuleType

from core.llm_client import LLMClient
from core.approval_manager import ApprovalManager
from config.settings import BASE_DIR
from services.workspace_manager import WorkspaceManager
from services.code_executor import CodeExecutor


class Project1Adapter:
    """Adapter connecting Project 1 coding capabilities to Project 2."""

    _import_lock = threading.RLock()
    _context_lock = threading.RLock()

    BLOCKED_FUNCTIONS = {
        "build_program",
        "execute_program",
        "debug_program",
    }

    def __init__(
        self,
        llm_client: LLMClient,
        workspace_manager: WorkspaceManager | None = None,
        project1_dir: Path | str | None = None,
        code_executor: CodeExecutor | None = None,
        approval_manager: ApprovalManager | None = None,
    ):
        if llm_client is None:
            raise ValueError("A shared LLM client is required.")

        self.llm_client = llm_client
        self.workspace_manager = workspace_manager or WorkspaceManager()
        self.approval_manager = approval_manager or ApprovalManager()

        # Both components share the same approval manager.
        self.code_executor = code_executor or CodeExecutor(
            workspace_manager=self.workspace_manager,
            approval_manager=self.approval_manager,
        )

        self.project1_dir = Path(
            project1_dir or BASE_DIR / "vendor" / "CodePilot"
        ).resolve()

        if not self.project1_dir.is_dir():
            raise FileNotFoundError(
                f"Project 1 source directory not found: {self.project1_dir}"
            )

        agent_path = self.project1_dir / "agent.py"
        llm_path = self.project1_dir / "llm.py"
        tools_path = self.project1_dir / "tools.py"

        for path in (agent_path, llm_path, tools_path):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Required Project 1 source file not found: {path}"
                )

        self.agent = self._load_agent(agent_path, llm_path, tools_path)
        self._verify_agent_api()

    def _load_module(
        self,
        module_name: str,
        module_path: Path,
    ) -> ModuleType:
        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
        )

        if spec is None or spec.loader is None:
            raise ImportError(
                f"Unable to load Project 1 module: {module_path}"
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise

        return module

    def _load_agent(
        self,
        agent_path: Path,
        llm_path: Path,
        tools_path: Path,
    ) -> ModuleType:
        with self._import_lock:
            saved_modules = {
                name: sys.modules.get(name)
                for name in ("llm", "tools")
            }

            try:
                llm_module = self._load_module("llm", llm_path)
                self._load_module("tools", tools_path)
                llm_module.ask_model = self._ask_model_bridge

                return self._load_module(
                    "codepilot_project1_agent",
                    agent_path,
                )

            finally:
                for name, previous in saved_modules.items():
                    if previous is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = previous

    def _ask_model_bridge(self, prompt: str) -> str:
        return self.llm_client.generate_response(
            system_prompt=(
                "You are CodePilot, an expert software engineering "
                "and Python coding assistant. Never claim that code "
                "was saved or executed."
            ),
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=8000,
        )

    def _verify_agent_api(self):
        for name in ("generate_code", "analyse_error", "fix_code"):
            if not callable(getattr(self.agent, name, None)):
                raise ImportError(f"Project 1 API is missing: {name}")

        for name in self.BLOCKED_FUNCTIONS:
            if not callable(getattr(self.agent, name, None)):
                raise ImportError(
                    f"Expected Project 1 function not found: {name}"
                )

    def _validate_workspace(self, workspace: Path | str) -> Path:
        return self.workspace_manager._resolve_project_dir(workspace)

    def generate_code(self, task: str, workspace: Path | str) -> str:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Coding task cannot be empty.")

        project_dir = self._validate_workspace(workspace)

        with self._context_lock:
            original_reader = self.agent.read_project_context

            try:
                self.agent.read_project_context = (
                    lambda max_files=10:
                    self.workspace_manager.get_project_context(
                        project_dir,
                        max_files=max_files,
                    )
                )

                generated_code = self.agent.generate_code(task)

            finally:
                self.agent.read_project_context = original_reader

        if not isinstance(generated_code, str) or not generated_code.strip():
            raise RuntimeError("Project 1 returned empty generated code.")

        return self._strip_code_fences(generated_code)

    def analyse_error(self, code: str, error_message: str) -> str:
        if not code.strip() or not error_message.strip():
            raise ValueError("Code and error message are required.")

        return self.agent.analyse_error(code, error_message)

    def fix_code(self, code: str, error_analysis: str) -> str:
        if not code.strip() or not error_analysis.strip():
            raise ValueError("Code and error analysis are required.")

        corrected = self.agent.fix_code(code, error_analysis)

        if not isinstance(corrected, str) or not corrected.strip():
            raise RuntimeError("Project 1 returned empty corrected code.")

        return self._strip_code_fences(corrected)

    def fix_errors(
        self,
        error_report: dict,
        workspace: Path | str,
    ) -> str:
        """Correct a workspace file using Project 1 debugging functions."""

        if not isinstance(error_report, dict):
            raise ValueError("Error report must be a dictionary.")

        filename = error_report.get("filename")
        error_message = error_report.get("error")

        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Error report must contain a filename.")

        if not isinstance(error_message, str) or not error_message.strip():
            raise ValueError("Error report must contain an error message.")

        project_dir = self._validate_workspace(workspace)
        code = self.workspace_manager.read_file(project_dir, filename)

        analysis = self.analyse_error(code, error_message)
        corrected = self.fix_code(code, analysis)

        self.workspace_manager.validate_python_code(corrected)

        self.workspace_manager.write_file(
            project_dir,
            filename,
            corrected,
            overwrite=True,
        )

        return corrected

    def execute_code(
        self,
        workspace: Path | str,
        filename: str,
        approval_id: str,
    ):
        """Execute workspace code after explicit approval."""

        project_dir = self._validate_workspace(workspace)

        if not self.approval_manager.is_approved(approval_id):
            raise PermissionError(
                "Code execution has not been approved."
            )

        return self.code_executor.execute_file(
            project_dir,
            filename,
            approval_id=approval_id,
        )

    @staticmethod
    def _strip_code_fences(code: str) -> str:
        lines = code.strip().splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        return "\n".join(lines).strip()
