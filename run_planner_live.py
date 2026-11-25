import json
from pathlib import Path

from core.llm_client import LLMClient
from agents.planner_agent import PlannerAgent

ROOT = Path(__file__).resolve().parent

requirements_path = ROOT / "requirements.md"
architecture_path = ROOT / "architecture.md"

if not requirements_path.exists():
    raise FileNotFoundError("requirements.md not found in the project root.")

if not architecture_path.exists():
    raise FileNotFoundError("architecture.md not found in the project root.")

requirements = requirements_path.read_text(encoding="utf-8")
architecture = architecture_path.read_text(encoding="utf-8")

print("Initializing Planner Agent...")
planner = PlannerAgent(llm_client=LLMClient())

print("Generating implementation plan from real project documents...")
plan = planner.generate_plan(
    requirements=requirements,
    architecture=architecture,
)

output_path = ROOT / "implementation_plan.json"
output_path.write_text(
    json.dumps(plan, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("\nSUCCESS: Implementation plan generated and validated.")
print(f"Saved to: {output_path}")
print(f"Number of tasks: {len(plan.get('tasks', []))}")
print("\nExecution order:")
for index, task_id in enumerate(plan.get("execution_order", []), start=1):
    print(f"{index}. {task_id}")
