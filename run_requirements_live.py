
from core.llm_client import LLMClient
from agents.requirements_agent import RequirementsAgent


def main():
    print("\nInitializing CodePilot Requirements Agent...")

    llm_client = LLMClient()
    agent = RequirementsAgent(llm_client=llm_client)

    user_request = """
    Build a pharmacy inventory management application
    with billing, stock tracking and expiry alerts.
    """

    print("\nSending request to the AI model...")
    print("Please wait...\n")

    try:
        result = agent.analyze_requirements(user_request)

        print("=" * 70)
        print("CODEPILOT - GENERATED REQUIREMENTS DOCUMENT")
        print("=" * 70)

        print(result)

        print("\n" + "=" * 70)
        print("Saving requirements.md...")

        with open(
            "requirements.md",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(result)

        print("SUCCESS: requirements.md generated!")

    except Exception as error:
        print(f"\nERROR: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
