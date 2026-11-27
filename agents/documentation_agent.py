
"""Generate project documentation from actual implementation details."""

import json
from pathlib import Path

from core.base_agent import BaseAgent
from schemas.agent_response import AgentResponse, AgentStatus
from services.workspace_manager import WorkspaceManager


class DocumentationAgent(BaseAgent):
    """Generate README, installation and technical documentation."""

    DOCUMENT_FILES = {
        "README.md": "readme",
        "installation_guide.md": "installation_guide",
        "technical_summary.md": "technical_summary",
    }

    @property
    def system_prompt(self):
        return """
        You are CodePilot's Documentation Agent.

        Generate accurate, professional software documentation
        using actual project files, architecture and test results.

        Never invent features, dependencies, APIs or test results.
        Never include passwords, API keys, tokens or secrets.

        Return the requested documentation in valid JSON format.
        """

    def __init__(self, llm_client, workspace_manager=None):
        super().__init__(
            name="Documentation Agent",
            role="Software Documentation Specialist",
            description=(
                "Generates accurate project documentation from "
                "implementation files and test results."
            ),
            llm_client=llm_client,
        )

        self.workspace_manager = (
            workspace_manager or WorkspaceManager()
        )

    def _collect_project_context(self, workspace, max_files=20):
        files = self.workspace_manager.list_files(workspace)

        context = {
            "files": files,
            "source_files": {},
        }

        supported_extensions = {
            ".py", ".txt", ".json", ".toml", ".yaml", ".yml"
        }

        for filename in files:
            if len(context["source_files"]) >= max_files:
                break

            path = Path(filename)

            if path.suffix.lower() not in supported_extensions:
                continue

            try:
                content = self.workspace_manager.read_file(
                    workspace,
                    filename,
                )
                context["source_files"][filename] = content[:8000]

            except Exception:
                continue

        return context

    @staticmethod
    def _parse_documentation(response_text):
        text = response_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        data = json.loads(text)

        if not isinstance(data, dict):
            raise ValueError("Documentation response must be a JSON object.")

        return data

    def generate_documentation(
        self,
        workspace,
        requirements="",
        architecture="",
        testing_results=None,
    ):
        try:
            project_dir = self.workspace_manager._resolve_project_dir(
                workspace
            )

            context = self._collect_project_context(project_dir)
            project_name = project_dir.name

            prompt = f"""
Generate accurate documentation for this implemented project.

PROJECT NAME:
{project_name}

ORIGINAL REQUIREMENTS:
{requirements or "Not provided"}

ARCHITECTURE:
{architecture or "Not provided"}

PROJECT FILE LIST:
{json.dumps(context["files"], indent=2)}

ACTUAL SOURCE CODE AND CONFIGURATION:
{json.dumps(context["source_files"], indent=2)}

TESTING RESULTS:
{json.dumps(testing_results or {}, indent=2, default=str)}

Generate exactly three Markdown documents.

1. README.md:
- Project overview
- Actual implemented features
- Technology stack
- Project structure
- How to run the application
- Testing instructions

2. installation_guide.md:
- Prerequisites
- Python version if identifiable
- Dependency installation
- Environment configuration
- Setup and startup instructions
- Troubleshooting

3. technical_summary.md:
- System overview
- Architecture
- Module responsibilities
- Main application flow
- Database details if identifiable
- Testing results
- Known limitations

RULES:
- Document only features supported by the supplied files.
- Do not invent APIs, dependencies or functionality.
- Clearly identify unverifiable information.
- Never include passwords, API keys or secrets.
- Never claim tests passed without supporting results.
- Return valid JSON only, without Markdown code fences.

Required JSON structure:
{{
    "readme": "Complete README Markdown content",
    "installation_guide": "Complete installation guide Markdown content",
    "technical_summary": "Complete technical summary Markdown content"
}}
"""

            response_text = self.run(prompt)
            documents = self._parse_documentation(response_text)

            missing = (
                set(self.DOCUMENT_FILES.values())
                - set(documents.keys())
            )

            if missing:
                raise ValueError(
                    f"Missing documentation sections: {sorted(missing)}"
                )

            saved_files = []

            for filename, key in self.DOCUMENT_FILES.items():
                content = documents[key]

                if not isinstance(content, str) or not content.strip():
                    raise ValueError(
                        f"Generated document is empty: {filename}"
                    )

                self.workspace_manager.write_file(
                    project_dir,
                    filename,
                    content.strip() + "\n",
                    overwrite=True,
                )

                saved_files.append(filename)

            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output=(
                    "Project documentation generated successfully: "
                    + ", ".join(saved_files)
                ),
                metadata={
                    "project_name": project_name,
                    "documentation_files": saved_files,
                    "project_file_count": len(context["files"]),
                    "source_files_inspected": list(
                        context["source_files"].keys()
                    ),
                },
            )

        except Exception as exc:
            return AgentResponse(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                output="Documentation generation failed.",
                error=str(exc),
                metadata={"documentation_files": []},
            )
