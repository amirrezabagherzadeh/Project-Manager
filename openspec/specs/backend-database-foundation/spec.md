# backend-database-foundation Specification

## Purpose

Provide a migrated, asynchronous persistence boundary with portable integrity rules
and predictable transaction behavior for all backend domain phases.

## Requirements

### Requirement: Async database lifecycle
The backend SHALL provide request-scoped asynchronous database sessions and SHALL
dispose database connections during application shutdown without creating schema at
application startup.

#### Scenario: Request obtains a session
- **GIVEN** the application is running against a migrated database
- **WHEN** an API dependency requests a database session
- **THEN** it receives one asynchronous session scoped to the request

#### Scenario: Application shuts down
- **GIVEN** the application has opened database connections
- **WHEN** application shutdown completes
- **THEN** the database engine is disposed without dropping or recreating schema

### Requirement: Service-owned atomic transactions
The backend SHALL commit a compound write only after its service operation succeeds
and SHALL roll back the complete transaction when any part fails.

#### Scenario: Compound write succeeds
- **GIVEN** a service operation performs multiple related persistence writes
- **WHEN** every business rule and persistence step succeeds
- **THEN** all writes become visible in one committed transaction

#### Scenario: Compound write fails
- **GIVEN** a service operation has staged one or more writes
- **WHEN** a later rule or persistence step fails
- **THEN** none of that operation's staged writes remain committed

### Requirement: Portable identity and time conventions
Persisted domain entities SHALL use UUID identifiers and offset-aware UTC timestamps,
and SQLite foreign-key enforcement SHALL be enabled for every application and
migration connection.

#### Scenario: Entity is persisted
- **GIVEN** a new persisted identity entity
- **WHEN** it is committed
- **THEN** its identifier is a UUID and its timestamps represent UTC

#### Scenario: Invalid foreign key is written
- **GIVEN** a record references a missing parent
- **WHEN** the write is flushed or committed
- **THEN** the database rejects the write with no orphan record

### Requirement: Alembic is the schema authority
The backend SHALL create and change domain schema only through reversible Alembic
migrations and SHALL support applying the complete migration chain to an empty,
explicitly disposable database.

#### Scenario: Empty database is upgraded
- **GIVEN** an empty disposable database
- **WHEN** `alembic upgrade head` runs
- **THEN** all Phase 1 tables, foreign keys, unique constraints, and indexes exist

#### Scenario: Phase 1 migration is rolled back
- **GIVEN** a disposable database at the Phase 1 revision
- **WHEN** the Phase 1 downgrade runs and the revision is applied again
- **THEN** downgrade and re-upgrade both succeed without application schema creation

