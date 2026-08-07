## Purpose

Provide a minimal observable API foundation that proves the Backend can start, report health, and publish its contract before domain capabilities are added.

## ADDED Requirements

### Requirement: Backend health
The Backend SHALL expose a health endpoint that returns a successful machine-readable response when the application is ready to accept requests.

#### Scenario: Healthy application
- **GIVEN** the Backend has started successfully
- **WHEN** a client requests `/health`
- **THEN** the service returns a successful status and a stable health payload

### Requirement: API documentation
The Backend SHALL publish Swagger UI, ReDoc, and an OpenAPI document at the project-defined paths in development.

#### Scenario: Developer opens Swagger
- **GIVEN** the Backend is running in development
- **WHEN** a developer opens `/docs`
- **THEN** Swagger UI loads and includes the health operation with correct metadata

#### Scenario: Production documentation policy
- **GIVEN** API documentation is disabled by production configuration
- **WHEN** an unauthenticated client requests a documentation path
- **THEN** the documentation is not exposed

### Requirement: Backend quality baseline
The Backend SHALL have automated formatting, linting, type-checking, and test entry points that fail with a non-zero status when violations are found.

#### Scenario: Clean foundation is verified
- **GIVEN** the Phase 0 Backend files are installed
- **WHEN** the documented backend quality gate runs
- **THEN** all configured checks complete successfully

