
# CodePilot: Agentic Software Factory
## System Architecture

### 1. Project Overview

CodePilot is an agentic AI software engineering platform designed to automate major stages of the software development lifecycle.

It uses multiple specialized AI agents coordinated by a central orchestrator. Each agent performs a specific responsibility, while the orchestrator manages task execution, workflow progression, and communication between agents.

### 2. High-Level Architecture

The system consists of the following layers:

1. Presentation Layer
   - Streamlit user interface
   - Project input and configuration
   - Workflow status and progress display
   - Human approval checkpoints

2. Orchestration Layer
   - Central Orchestrator
   - Task Manager
   - State Manager
   - Approval Manager

3. Specialized Agent Layer
   - Requirements Agent
   - Architect Agent
   - Planner Agent
   - Coding Agent
   - Testing Agent
   - Debugging Agent
   - Documentation Agent

4. Shared Services Layer
   - LLM Client
   - Workspace Manager
   - Code Executor
   - Project 1 Adapter
   - Report Generator

5. Data and Model Layer
   - Pydantic schemas
   - Task models
   - Workflow state
   - Project files and generated artifacts

### 3. Agent Responsibilities

| Agent | Responsibility |
|---|---|
| Requirements Agent | Understands user requirements and produces structured specifications. |
| Architect Agent | Designs the software architecture and identifies components. |
| Planner Agent | Converts requirements and architecture into implementation tasks. |
| Coding Agent | Generates and modifies project source code. |
| Testing Agent | Creates and executes tests to evaluate generated code. |
| Debugging Agent | Analyzes failures and proposes corrections. |
| Documentation Agent | Generates technical documentation and reports. |

### 4. Central Orchestrator

The Orchestrator coordinates the complete development workflow.

Its responsibilities include:

- Accepting project requests.
- Assigning tasks to specialized agents.
- Managing task dependencies and execution order.
- Tracking workflow state.
- Enforcing approval checkpoints.
- Coordinating testing and debugging.
- Managing completion and reporting.

### 5. Shared Infrastructure

All specialized agents use the shared LLM Client for AI communication.

The Workspace Manager manages generated project files. The Code Executor handles controlled code execution. The Project 1 Adapter provides a defined integration boundary for capabilities from the earlier project.

### 6. Human-in-the-Loop Design

CodePilot includes human approval checkpoints before sensitive operations.

The user should be able to review proposed plans and generated changes before they are accepted or executed.

### 7. Safety and Reliability

The system is designed with the following safeguards:

- API keys stored in environment variables.
- Workspace path validation.
- Controlled code execution with timeouts.
- Human approval for sensitive operations.
- Test-driven validation of generated code.
- Limited debugging retries.
- Clear workflow state and error reporting.

Code execution controls are safeguards, not a guarantee of complete operating-system isolation.

### 8. Technology Stack

- Language: Python
- User Interface: Streamlit
- AI Integration: OpenAI Python SDK with OpenRouter
- Data Validation: Pydantic
- Configuration: python-dotenv
- Testing: pytest
- Version Control: Git and GitHub

### 9. Architectural Objective

The architecture separates user interaction, orchestration, agent responsibilities, and shared services.

This modular design supports independent agent development, easier testing, maintainability, and future integration of additional software engineering capabilities.
