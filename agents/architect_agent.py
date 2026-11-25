
from core.base_agent import BaseAgent
from core.llm_client import LLMClient


class ArchitectAgent(BaseAgent):
    """Designs software architecture and database structures."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="Architect Agent",
            role="Software Architecture and Database Design",
            llm_client=llm_client,
            description=(
                "Transforms approved software requirements into "
                "system architecture and database design documents."
            ),
        )

    @property
    def system_prompt(self) -> str:
        return """
You are the Software Architect Agent in CodePilot,
an Agentic Software Factory.

Your responsibility is to transform a Software Requirements
Specification into professional technical design documents.

ARCHITECTURE RULES:

1. Use the supplied requirements as the source of truth.
2. Distinguish confirmed requirements from assumptions.
3. Never silently promote assumptions into confirmed features.
4. Do not invent integrations, technologies, user roles,
   business rules, or compliance obligations.
5. If a technical decision is not specified, recommend an
   option and clearly label it as a recommendation.
6. Explain important design trade-offs.
7. Ensure every major component supports a stated requirement.
8. Do not create implementation task lists.
9. Use professional Markdown.
10. Return only the requested document.
"""

    def _validate_document(
        self,
        document: str,
        expected_heading: str,
        required_sections: list[str],
        document_name: str,
    ) -> str:

        if not isinstance(document, str) or not document.strip():
            raise RuntimeError(
                f"Architect Agent returned an empty {document_name}."
            )

        if not document.lstrip().startswith(expected_heading):
            raise RuntimeError(
                f"Architect Agent returned an invalid {document_name}. "
                f"Expected heading: {expected_heading}"
            )

        missing_sections = [
            section
            for section in required_sections
            if section not in document
        ]

        if missing_sections:
            raise RuntimeError(
                f"Architect Agent returned an incomplete {document_name}. "
                "Missing sections: " + ", ".join(missing_sections)
            )

        return document.strip()

    def generate_architecture(self, requirements: str) -> str:
        """Generate a system architecture document."""

        if not isinstance(requirements, str) or not requirements.strip():
            raise ValueError("Requirements document cannot be empty.")

        user_prompt = f"""
Create a professional System Architecture Document
using the following Software Requirements Specification.

Do not invent confirmed requirements.

DOCUMENT STRUCTURE:

# System Architecture Document

## 1. Architecture Overview
Describe the proposed architecture and its purpose.

## 2. Architecture Style
Identify and justify the recommended architecture style.

## 3. Technology Stack
List recommended technologies. Distinguish recommendations
from confirmed choices.

## 4. System Components
Describe major components and responsibilities.

## 5. Component Interactions
Explain how components communicate.

## 6. Data Flow
Describe important application data flows.

## 7. Security Considerations
Discuss relevant considerations. Mark unspecified decisions
as recommendations.

## 8. Scalability and Reliability
Discuss relevant considerations without inventing targets.

## 9. Architecture Decisions and Trade-offs
Explain important design choices and alternatives.

## 10. Assumptions and Open Decisions
List assumptions and decisions requiring confirmation.

Keep the document focused and technically specific.

SOURCE REQUIREMENTS:

{requirements.strip()}
"""

        result = self.run(user_prompt)

        return self._validate_document(
            document=result,
            expected_heading="# System Architecture Document",
            required_sections=[
                "## 1. Architecture Overview",
                "## 2. Architecture Style",
                "## 3. Technology Stack",
                "## 4. System Components",
                "## 5. Component Interactions",
                "## 6. Data Flow",
                "## 7. Security Considerations",
                "## 8. Scalability and Reliability",
                "## 9. Architecture Decisions and Trade-offs",
                "## 10. Assumptions and Open Decisions",
            ],
            document_name="architecture document",
        )

    def generate_database_design(self, requirements: str) -> str:
        """Generate a concise database design document."""

        if not isinstance(requirements, str) or not requirements.strip():
            raise ValueError("Requirements document cannot be empty.")

        user_prompt = f"""
Create a professional Database Design Document based on
the supplied Software Requirements Specification.

IMPORTANT:
- Use the requirements as the source of truth.
- Do not invent confirmed entities, fields, or relationships.
- Clearly label proposed entities and design assumptions.
- If information is unavailable, write "Not specified".
- Keep the entire document concise, approximately
  1,000–1,400 words.
- Use compact tables and bullet points where appropriate.
- Include all ten sections below.
- Do not repeat the requirements document.

DOCUMENT STRUCTURE:

# Database Design Document

## 1. Database Overview
Briefly explain the proposed database approach.

## 2. Database Technology
Recommend a suitable technology and explain why.
Label it as a recommendation if unspecified.

## 3. Entity Overview
List proposed entities and their purposes.

## 4. Entity Attributes
Use a compact table:
Entity | Attribute | Suggested Type | Description

## 5. Primary and Foreign Keys
Identify proposed keys.

## 6. Entity Relationships
Explain relationships and cardinalities.

## 7. Data Integrity Constraints
Describe relevant validation and integrity rules.

## 8. Indexing Strategy
Recommend relevant indexes and explain their purpose.

## 9. Data Security and Backup Considerations
Discuss relevant considerations without inventing
confirmed requirements.

## 10. Assumptions and Open Decisions
List decisions requiring stakeholder confirmation.

SOURCE REQUIREMENTS:

{requirements.strip()}
"""

        result = self.run(user_prompt)

        return self._validate_document(
            document=result,
            expected_heading="# Database Design Document",
            required_sections=[
                "## 1. Database Overview",
                "## 2. Database Technology",
                "## 3. Entity Overview",
                "## 4. Entity Attributes",
                "## 5. Primary and Foreign Keys",
                "## 6. Entity Relationships",
                "## 7. Data Integrity Constraints",
                "## 8. Indexing Strategy",
                "## 9. Data Security and Backup Considerations",
                "## 10. Assumptions and Open Decisions",
            ],
            document_name="database design document",
        )
