# backend-delivery-program Specification

## Purpose
Provide an observable, phase-gated delivery contract for implementing and verifying
the complete FastAPI backend defined by Backend PRD 1.1 without advancing past an
unfinished prerequisite or claiming completion without evidence.
## Requirements
### Requirement: Phase 0 completion gates backend implementation
The backend delivery program SHALL keep every Phase 1 implementation task blocked
until all Phase 0 tasks and quality gates, including Compose verification task 4.2,
are complete.

#### Scenario: Phase 0 is incomplete
- **GIVEN** one or more Phase 0 tasks or required validations are incomplete
- **WHEN** the backend delivery program evaluates its implementation preflight
- **THEN** it records the incomplete task or failed command and performs no Phase 1
  code or schema change

#### Scenario: Phase 0 is verified
- **GIVEN** every Phase 0 task is checked and its required validation has passed
- **WHEN** strict OpenSpec validation and the Phase 0 completion review succeed
- **THEN** the program permits creation of the Phase 1 implementation change

### Requirement: Backend phases are delivered sequentially
The backend delivery program SHALL deliver exactly one active implementation phase
at a time in the order defined by Backend PRD 1.1 and `AGENTS.md`.

#### Scenario: Current phase remains incomplete
- **GIVEN** the active backend phase has an unchecked task, failed gate, unsynchronized
  specification, or unresolved critical or high-severity defect
- **WHEN** progression to the next phase is evaluated
- **THEN** the next phase change is not created or implemented

#### Scenario: Current phase is complete
- **GIVEN** the active phase satisfies every acceptance criterion and validation
- **WHEN** its delta specifications are synchronized and its change is archived
- **THEN** the next numbered backend phase becomes eligible for proposal creation

### Requirement: Every phase has an approved implementation contract
Before modifying runtime code for a backend phase, the program SHALL create and
strictly validate a phase-specific proposal, delta specifications, design, and
ordered task list that trace to the governing Backend PRD requirement and use cases.

#### Scenario: Phase artifacts are ready
- **GIVEN** the preceding phase gate has passed
- **WHEN** a new phase is proposed
- **THEN** its artifacts identify scope, non-goals, public contracts, migrations,
  permissions, failure behavior, tests, and rollback before implementation starts

#### Scenario: Phase artifacts are invalid
- **GIVEN** a required artifact is missing or strict OpenSpec validation fails
- **WHEN** implementation readiness is evaluated
- **THEN** runtime implementation remains blocked and the validation failure is
  recorded

### Requirement: Complete Backend PRD coverage is traceable
The program SHALL deliver BE-FR-01 through BE-FR-09 and the backend responsibilities
of UC-01 through UC-12 through the nine numbered backend changes defined by the
roadmap.

#### Scenario: Program coverage is audited
- **GIVEN** the nine phase-specific changes and Backend PRD 1.1
- **WHEN** traceability is reviewed
- **THEN** every in-scope functional requirement, endpoint group, data model,
  permission rule, migration, and acceptance flow maps to at least one verified
  phase task and test

#### Scenario: Requirement is missing
- **GIVEN** an in-scope PRD requirement has no phase task or acceptance evidence
- **WHEN** program completion is evaluated
- **THEN** the backend program remains incomplete

### Requirement: Phase completion is evidence-based
The program SHALL mark a phase task complete only after its named automated or
manual validation succeeds against the implemented behavior.

#### Scenario: Code exists but validation fails
- **GIVEN** implementation code has been written for a task
- **WHEN** the task's required test, migration, HTTP scenario, type check, lint,
  formatting, or runtime validation fails
- **THEN** the task remains unchecked and the root failure is recorded

#### Scenario: Phase gate succeeds
- **GIVEN** all phase tasks are checked and all required validations have succeeded
- **WHEN** the phase completion review runs
- **THEN** the result records commands, outcomes, changed contracts, migrations,
  and known non-critical limitations before archival

### Requirement: Public API contracts remain synchronized
Each phase that changes the API SHALL publish documented OpenAPI operations and
regenerate the committed frontend TypeScript schema without adding frontend feature
behavior.

#### Scenario: API contract changes
- **GIVEN** a phase adds or changes a public endpoint or schema
- **WHEN** the phase contract gate runs
- **THEN** `/api/v1/openapi.json` is valid, Swagger exposes the intended operation,
  the generated TypeScript schema is refreshed, and unexplained drift is rejected

### Requirement: Blockers are reported without false completion
The backend delivery program SHALL stop at a genuine external or information blocker
without claiming the affected task, phase, or complete backend is done.

#### Scenario: External blocker prevents a required gate
- **GIVEN** a required command cannot succeed because of a verified external
  dependency or environment limitation
- **WHEN** safe in-scope alternatives have been exhausted
- **THEN** the program records the exact blocker, affected task, attempted commands,
  observed output, and remaining work, and leaves the relevant task unchecked

