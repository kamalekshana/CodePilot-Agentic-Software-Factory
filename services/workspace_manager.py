
import ast
from pathlib import Path

from config.settings import WORKSPACE_DIR


class WorkspaceManager:
    """Manage isolated project workspaces and safely handle generated files."""

    BLOCKED_NAMES = {"secrets.toml"}
    MAX_FILE_SIZE = 1_000_000  # 1 MB

    def __init__(self, workspace_root: Path | str = WORKSPACE_DIR):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, project_name: str) -> Path:
        """Create and return a dedicated workspace for a project."""
        if not isinstance(project_name, str) or not project_name.strip():
            raise ValueError("Project name cannot be empty.")

        slug = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in project_name.strip()
        ).strip("_")

        if not slug:
            raise ValueError("Project name contains no valid characters.")

        project_dir = (self.workspace_root / slug).resolve()

        if not project_dir.is_relative_to(self.workspace_root):
            raise ValueError("Invalid project workspace path.")

        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def _resolve_project_dir(self, project_dir: Path | str) -> Path:
        """Validate that the project directory belongs to the workspace root."""
        path = Path(project_dir).resolve()

        if not path.is_relative_to(self.workspace_root):
            raise ValueError("Project directory is outside the workspace root.")

        if path == self.workspace_root:
            raise ValueError("A dedicated project workspace is required.")

        if not path.exists() or not path.is_dir():
            raise ValueError("Project workspace does not exist.")

        return path

    def _resolve_file_path(
        self,
        project_dir: Path | str,
        filename: str,
    ) -> Path:
        """Validate a relative filename and resolve it inside the workspace."""
        project_path = self._resolve_project_dir(project_dir)

        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Filename cannot be empty.")

        relative_path = Path(filename)

        if relative_path.is_absolute() or relative_path.drive:
            raise ValueError("Absolute file paths are not allowed.")

        if any(part == ".." for part in relative_path.parts):
            raise ValueError("Path traversal is not allowed.")

        if any(
            part.lower() in self.BLOCKED_NAMES
            or part.lower().startswith(".env")
            for part in relative_path.parts
        ):
            raise ValueError("Access to sensitive files is blocked.")

        file_path = (project_path / relative_path).resolve()

        if not file_path.is_relative_to(project_path):
            raise ValueError("File path is outside the project workspace.")

        return file_path

    def write_file(
        self,
        project_dir: Path | str,
        filename: str,
        content: str,
        overwrite: bool = False,
    ) -> Path:
        """Validate and save a generated file inside its project workspace."""
        if not isinstance(content, str):
            raise ValueError("File content must be text.")

        if len(content.encode("utf-8")) > self.MAX_FILE_SIZE:
            raise ValueError("File exceeds the 1 MB size limit.")

        file_path = self._resolve_file_path(project_dir, filename)

        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {filename}")

        if file_path.exists() and not file_path.is_file():
            raise ValueError("Target path is not a regular file.")

        if file_path.suffix.lower() == ".py":
            self.validate_python_code(content)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def read_file(
        self,
        project_dir: Path | str,
        filename: str,
    ) -> str:
        """Read a file after validating its workspace location."""
        file_path = self._resolve_file_path(project_dir, filename)

        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File not found: {filename}")

        if file_path.stat().st_size > self.MAX_FILE_SIZE:
            raise ValueError("File exceeds the 1 MB size limit.")

        return file_path.read_text(encoding="utf-8")

    def list_files(self, project_dir: Path | str) -> list[str]:
        """List project files while excluding sensitive and temporary paths."""
        project_path = self._resolve_project_dir(project_dir)

        ignored_directories = {
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
        }

        files = []

        for path in sorted(project_path.rglob("*")):
            relative_path = path.relative_to(project_path)

            if any(
                part.lower() in ignored_directories
                for part in relative_path.parts
            ):
                continue

            if any(
                part.lower() in self.BLOCKED_NAMES
                or part.lower().startswith(".env")
                for part in relative_path.parts
            ):
                continue

            if path.is_file():
                files.append(relative_path.as_posix())

        return files

    def get_project_context(
        self,
        project_dir: Path | str,
        max_files: int = 10,
    ) -> str:
        """Read a limited amount of safe source context for code generation."""
        if not isinstance(max_files, int) or max_files < 1:
            raise ValueError("max_files must be a positive integer.")

        project_path = self._resolve_project_dir(project_dir)
        allowed_extensions = {".py", ".txt", ".md", ".json"}
        context = []

        for filename in self.list_files(project_path):
            if len(context) >= max_files:
                break

            if Path(filename).suffix.lower() not in allowed_extensions:
                continue

            try:
                content = self.read_file(project_path, filename)
            except (OSError, ValueError, UnicodeDecodeError):
                continue

            context.append(
                f"\n--- FILE: {filename} ---\n{content}"
            )

        if not context:
            return "No relevant project files found."

        return "\n".join(context)

    @staticmethod
    def validate_python_code(code: str) -> bool:
        """Validate Python syntax without executing the source code."""
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Python source code cannot be empty.")

        try:
            ast.parse(code)
        except SyntaxError as error:
            raise ValueError(
                f"Python syntax error on line {error.lineno}: {error.msg}"
            ) from error

        return True
