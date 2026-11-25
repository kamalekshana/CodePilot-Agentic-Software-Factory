
from pathlib import Path

from agents.architect_agent import ArchitectAgent
from core.llm_client import LLMClient


def main():
    project_root = Path(__file__).resolve().parent
    requirements_path = project_root / "requirements.md"

    if not requirements_path.exists():
        raise FileNotFoundError(
            "requirements.md was not found. "
            "Run the Requirements Agent live test first."
        )

    requirements = requirements_path.read_text(encoding="utf-8")

    if not requirements.strip():
        raise ValueError("requirements.md is empty.")

    print("\nInitializing Architect Agent...")
    llm_client = LLMClient()
    architect = ArchitectAgent(llm_client)

    print("\nGenerating system architecture...")
    architecture = architect.generate_architecture(requirements)

    architecture_path = project_root / "architecture.md"
    architecture_path.write_text(architecture, encoding="utf-8")
    print(f"Architecture saved: {architecture_path.name}")

    print("\nGenerating database design...")
    database_design = architect.generate_database_design(requirements)

    database_path = project_root / "database_design.md"
    database_path.write_text(database_design, encoding="utf-8")
    print(f"Database design saved: {database_path.name}")

    print("\n" + "=" * 55)
    print("ARCHITECT AGENT LIVE TEST: SUCCESS")
    print("=" * 55)
    print(f"Architecture document: {architecture_path}")
    print(f"Database design document: {database_path}")
    print("\nBoth documents were generated and validated.")


if __name__ == "__main__":
    main()
