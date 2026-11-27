
import json

from agents.documentation_agent import DocumentationAgent
from schemas.agent_response import AgentStatus
from services.workspace_manager import WorkspaceManager


class FakeLLMClient:
    def generate_response(self, system_prompt, user_prompt):
        return json.dumps({
            "readme": "# Demo Project\n\nProject overview.",
            "installation_guide": "# Installation\n\nInstall dependencies.",
            "technical_summary": "# Technical Summary\n\nSystem architecture.",
        })


class TestDocumentationAgent:

    def setup_method(self):
        self.workspace_manager = WorkspaceManager(
            "workspace_test_docs"
        )
        self.workspace = self.workspace_manager.create_workspace(
            "Documentation_Test_Project"
        )

        self.agent = DocumentationAgent(
            llm_client=FakeLLMClient(),
            workspace_manager=self.workspace_manager,
        )

    def test_generate_documentation(self):
        result = self.agent.generate_documentation(
            workspace=self.workspace,
            requirements="Create a demo application.",
            architecture="Simple Python application.",
            testing_results={"execution_status": "passed"},
        )

        assert result.status == AgentStatus.SUCCESS

        expected_files = [
            "README.md",
            "installation_guide.md",
            "technical_summary.md",
        ]

        for filename in expected_files:
            content = self.workspace_manager.read_file(
                self.workspace,
                filename,
            )
            assert content.strip()

    def test_invalid_llm_response(self):
        self.agent.run = lambda prompt: "invalid JSON"

        result = self.agent.generate_documentation(
            workspace=self.workspace
        )

        assert result.status == AgentStatus.FAILED

    def test_empty_document_rejected(self):
        self.agent.run = lambda prompt: json.dumps({
            "readme": "",
            "installation_guide": "# Installation",
            "technical_summary": "# Summary",
        })

        result = self.agent.generate_documentation(
            workspace=self.workspace
        )

        assert result.status == AgentStatus.FAILED
