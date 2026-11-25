
from core.llm_client import LLMClient
from services.planning_workflow import PlanningWorkflow


def main():
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
        llm_client = LLMClient()

        workflow = PlanningWorkflow.from_llm_client(
            llm_client=llm_client
        )

        print("\nStarting sequential planning workflow...")
        print("1. Requirements Agent")
        print("2. Architect Agent")
        print("3. Database Design")
        print("4. Planner Agent")

        result = workflow.run(
            project_name=project_name,
            user_request=user_request,
        )

        print("\n==============================================")
        print("       PLANNING WORKFLOW COMPLETED")
        print("==============================================")

        print(f"\nProject: {result['project_name']}")
        print(f"Output directory: {result['project_directory']}")

        print("\nGenerated artifacts:")
        for name, path in result["artifacts"].items():
            print(f"- {name}: {path}")

        plan = result["implementation_plan"]
        print(f"\nTotal implementation tasks: {len(plan['tasks'])}")

        print("\nCodePilot planning completed successfully!")

    except Exception as error:
        print(f"\nWorkflow failed: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
