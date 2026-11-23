
# CodePilot: Agentic Software Factory
## End-to-End Workflow

### 1. Workflow Overview

CodePilot follows a structured software development lifecycle in which specialized AI agents collaborate under the control of a central Orchestrator.

The workflow transforms a user's software requirements into a tested and documented software project.

### 2. Main Workflow Stages

#### Stage 1: User Input
The user submits a software project description through the Streamlit interface.

The system receives the project requirements and initializes a new workflow.

#### Stage 2: Requirements Analysis
The Requirements Agent:
- Analyzes the user's request.
- Identifies functional requirements.
- Identifies non-functional requirements.
- Detects missing or unclear information.
- Produces a structured requirements specification.

#### Stage 3: Architecture Design
The Architect Agent:
- Reviews the requirements.
- Identifies system components.
- Defines component responsibilities.
- Designs the application architecture.
- Produces an architecture specification.

#### Stage 4: Implementation Planning
The Planner Agent:
- Reviews the requirements and architecture.
- Breaks the project into manageable tasks.
- Identifies task dependencies.
- Establishes implementation order.
- Produces an implementation plan.

#### Stage 5: Human Approval
The Orchestrator presents the proposed plan for user review.

The workflow proceeds after the required approval is received.

#### Stage 6: Code Generation
The Coding Agent:
- Receives approved implementation tasks.
- Generates source code.
- Creates or modifies project files.
- Works within the designated workspace.

#### Stage 7: Testing
The Testing Agent:
- Reviews generated code.
- Creates relevant test cases.
- Executes tests through the testing services.
- Reports failures and successful results.

#### Stage 8: Debugging and Correction
If tests fail, the Debugging Agent:
- Analyzes error messages.
- Identifies potential causes.
- Proposes code corrections.
- Sends corrections through the controlled workflow.

The system allows a maximum of two debugging retries before reporting unresolved failures.

#### Stage 9: Final Validation
The system evaluates the corrected project and records its validation status.

Successful projects proceed to documentation.

Unresolved failures are reported to the user.

#### Stage 10: Documentation
The Documentation Agent:
- Summarizes the project.
- Describes its architecture.
- Documents implementation details.
- Records testing results.
- Produces technical documentation.

#### Stage 11: Final Delivery
The Orchestrator collects the completed artifacts and updates the workflow state.

The Streamlit interface presents the final project status and generated deliverables.

### 3. Workflow Sequence

User Input
    |
    v
Requirements Agent
    |
    v
Architect Agent
    |
    v
Planner Agent
    |
    v
Human Approval
    |
    v
Coding Agent
    |
    v
Testing Agent
    |
    v
Tests Passed? 
    |
    +---- Yes ----> Documentation Agent
    |
    +---- No -----> Debugging Agent
                         |
                         v
                  Correction Attempt
                         |
                         v
                    Re-testing
                         |
                         v
                 Maximum 2 Retries
                         |
                         v
                   Final Delivery

### 4. Orchestrator Responsibilities

The Orchestrator coordinates every stage and maintains the workflow state.

It is responsible for:
- Agent selection and task delegation.
- Workflow sequencing.
- Task dependency management.
- Approval coordination.
- Error handling.
- Retry management.
- Final status reporting.

### 5. Human Approval Checkpoints

Human involvement is required at important decision points, particularly before accepting implementation plans and applying sensitive code changes.

This keeps the user involved in decisions rather than allowing uncontrolled autonomous modifications.

### 6. Failure Handling

The workflow must handle:
- Missing or unclear requirements.
- LLM communication failures.
- Code generation errors.
- Test execution failures.
- Debugging failures.
- Approval rejection.
- Execution timeouts.

Errors should be recorded and communicated clearly.

### 7. Expected Outcome

The workflow aims to provide an integrated software engineering process covering requirements analysis, architecture design, planning, code generation, testing, debugging, and documentation through a coordinated multi-agent system.
