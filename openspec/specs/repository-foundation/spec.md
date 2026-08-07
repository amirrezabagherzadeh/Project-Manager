# repository-foundation Specification

## Purpose

Provide a reproducible repository baseline so a new engineer or automation agent can run, validate, and understand both applications without undocumented local knowledge.

## Requirements

### Requirement: Reproducible local setup
The repository SHALL document the required runtimes, environment setup, install commands, development commands, quality commands, and zero-to-running sequence for both applications.

#### Scenario: New developer follows the README
- **GIVEN** a supported machine with the documented runtimes
- **WHEN** a developer follows the setup instructions from a clean checkout
- **THEN** both applications start on their documented ports without requiring committed secrets

### Requirement: Environment and secret boundary
The repository SHALL provide safe environment examples and SHALL exclude runtime secrets, local databases, uploaded files, dependency directories, caches, and generated build output from version control.

#### Scenario: Environment examples are inspected
- **GIVEN** a clean checkout
- **WHEN** a developer reviews the environment templates
- **THEN** every required variable is described and no usable production credential is present

### Requirement: Phase-zero quality entry points
The repository SHALL expose stable commands for backend quality, frontend quality, migration, seed, development, and API client generation, even when later-phase commands are documented as not yet applicable.

#### Scenario: Foundation command inventory is reviewed
- **GIVEN** Phase 0 is complete
- **WHEN** an engineer reviews root tooling and documentation
- **THEN** each expected quality or development workflow has one canonical command
