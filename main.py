
"""CodePilot: Agentic Software Factory - Main Entry Point."""

import subprocess
import sys
from pathlib import Path

from core.llm_client import LLMClient
from services.software_factory import SoftwareFactory


BASE_DIR = Path(__file__).resolve().parent
PHARMACY_DIR = BASE_DIR / "workspace" / "Pharmacy_Inventory_Management"
PHARMACY_UI = PHARMACY_DIR / "task_012_user_interface_development.py"


def run_software_factory():
    """Run the complete planning and code-generation pipeline."""
    print("\n==============================================")
    print("   CODEPILOT: AGENTIC SOFTWARE FACTORY")
    print("==============================================\n")

    project_name = input("Enter project name: ").strip()
    user_request = input("\nDescribe the software you want to build:\n").strip()

    if not project_name or not user_request:
        print("\nError: Project name and requirements are required.")
        return

    try:
        print("\nInitializing AI agents...")
        factory = SoftwareFactory(LLMClient())

        print("\nStarting complete software factory workflow...")
        print("1. Requirements Agent")
        print("2. Architect Agent")
        print("3. Database Design")
        print("4. Planner Agent")
        print("5. Coding Agent")

        result = factory.run(
            project_name=project_name,
            user_request=user_request,
        )

        print("\n==============================================")
        print("       SOFTWARE FACTORY RESULT")
        print("==============================================")

        print(f"\nProject: {result['project_name']}")
        print(f"Workspace: {result['project_directory']}")
        print(f"Success: {result['success']}")

        print("\nGenerated files:")
        for filename in result["generated_files"]:
            print(f"- {filename}")

        if not result["success"]:
            print("\nCode generation did not complete successfully.")

    except Exception as error:
        print(f"\nWorkflow failed: {type(error).__name__}: {error}")


def run_pharmacy_application():
    """Launch the generated pharmacy application using Streamlit."""
    if not PHARMACY_UI.exists():
        print(f"\nPharmacy interface not found: {PHARMACY_UI}")
        return

    print("\nLaunching Pharmacy Inventory Management...")
    print("The Streamlit application will open in your browser.")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PHARMACY_UI),
        "--server.headless",
        "false",
    ]

    subprocess.run(command, cwd=str(PHARMACY_DIR), check=False)


def main():
    """Display the CodePilot application menu."""
    print("\n==============================================")
    print("   CODEPILOT: AGENTIC SOFTWARE FACTORY")
    print("==============================================")

    print("\n1. Run Software Factory")
    print("2. Launch Pharmacy Inventory Management")
    print("3. Exit")

    choice = input("\nSelect an option: ").strip()

    if choice == "1":
        run_software_factory()
    elif choice == "2":
        run_pharmacy_application()
    elif choice == "3":
        print("\nExiting CodePilot.")
    else:
        print("\nInvalid selection. Choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
