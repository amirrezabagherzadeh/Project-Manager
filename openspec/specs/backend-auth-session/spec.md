# backend-auth-session Specification

## Purpose

Provide a secure, documented identity and rotating-session contract that supports
registration, Swagger-compatible login, authenticated identity, refresh, and logout.

## Requirements

### Requirement: User registration
The API SHALL normalize email addresses to lowercase, require a name and a password
of at least ten characters, store only a one-way password hash, and return `201`
with public user data without creating a login session.

#### Scenario: Registration succeeds
- **GIVEN** a visitor supplies a valid name, unique mixed-case email, and valid password
- **WHEN** the visitor posts to `/api/v1/auth/register`
- **THEN** the API returns `201` in the single-success envelope with a lowercase email
- **AND** no access token or refresh cookie is issued

#### Scenario: Registration input is invalid
- **GIVEN** a visitor supplies an invalid email, blank name, or password shorter than ten characters
- **WHEN** registration is requested
- **THEN** the API returns `422 validation_error` and persists no user

#### Scenario: Email already exists
- **GIVEN** a user already exists for the normalized email
- **WHEN** another registration uses an equivalent email
- **THEN** the API returns `409 resource_conflict` and persists no duplicate

### Requirement: Swagger-compatible OAuth2 login
The API SHALL accept OAuth2 password form data at `/api/v1/auth/token`, use the form
username as the email, return a top-level bearer access token, set a rotating
refresh credential in an `HttpOnly` cookie, and publish a password-flow security
scheme usable by Swagger Authorize.

#### Scenario: Login succeeds
- **GIVEN** an active user supplies the correct normalized email and password as form data
- **WHEN** login is requested
- **THEN** the API returns `200` with top-level `access_token` and `token_type` equal to `bearer`
- **AND** it sets an environment-appropriate `HttpOnly` refresh cookie

#### Scenario: Credentials are invalid
- **GIVEN** the email is unknown or the password is incorrect
- **WHEN** login is requested
- **THEN** the API performs equivalent password-verification work and returns the same generic `401 invalid_credentials`
- **AND** it issues no token or refresh cookie

#### Scenario: Login content type is invalid
- **GIVEN** login credentials are not submitted as a valid OAuth2 form
- **WHEN** the token endpoint validates the request
- **THEN** the API returns the standard `422 validation_error` envelope

### Requirement: Access token security
Access tokens SHALL be 30-minute HS256 JWTs with `sub`, `iat`, `exp`, and unique
`jti` claims; validation SHALL pin the configured algorithm, require those claims,
and reject malformed, expired, or unknown-user tokens without exposing internals.

#### Scenario: Authenticated identity succeeds
- **GIVEN** an active user presents a valid unexpired access token
- **WHEN** `/api/v1/auth/me` is requested
- **THEN** the API returns the user's public data in the single-success envelope

#### Scenario: Bearer token is missing
- **GIVEN** no bearer credential is supplied
- **WHEN** a protected identity endpoint is requested
- **THEN** the API returns `401 authentication_required` with a Bearer challenge

#### Scenario: Access token is expired
- **GIVEN** a correctly signed token has passed its expiration
- **WHEN** a protected identity endpoint is requested
- **THEN** the API returns `401 token_expired` with no token claims or stack trace

#### Scenario: Access token is invalid
- **GIVEN** a token has a wrong algorithm, signature, required claim, subject, or shape
- **WHEN** a protected identity endpoint is requested
- **THEN** the API returns `401 authentication_required` without disclosing validation internals

### Requirement: Refresh sessions rotate and resist replay
The API SHALL use a cryptographically random opaque seven-day refresh credential,
store only its cryptographic hash, rotate it on every successful refresh, reject
expired or revoked sessions, and revoke the affected replacement chain when a
previously rotated credential is replayed.

#### Scenario: Refresh succeeds
- **GIVEN** a valid unexpired refresh cookie bound to an active session
- **WHEN** `/api/v1/auth/refresh` is requested from an allowed origin
- **THEN** the API atomically revokes the old session, links a replacement session,
  returns a new 30-minute access token, and replaces the cookie

#### Scenario: Rotated credential is replayed
- **GIVEN** a refresh credential was already rotated
- **WHEN** that old credential is submitted again
- **THEN** the API returns `401 authentication_required`, clears the refresh cookie,
  and revokes the affected replacement chain

#### Scenario: Refresh credential is expired, revoked, or unknown
- **GIVEN** the refresh cookie is expired, revoked, malformed, or absent
- **WHEN** refresh is requested
- **THEN** the API returns `401 authentication_required`, clears the cookie, and issues no access token

#### Scenario: Refresh origin is untrusted
- **GIVEN** a browser sends a refresh credential with a configured but untrusted Origin
- **WHEN** refresh is requested
- **THEN** the API returns `403 permission_denied` and does not rotate the session

### Requirement: Logout revokes the refresh session
The API SHALL revoke the presented refresh session when known, clear the refresh
cookie in all cases, and reveal no session existence.

#### Scenario: Authenticated session logs out
- **GIVEN** a valid refresh cookie
- **WHEN** `/api/v1/auth/logout` is requested from an allowed origin
- **THEN** the API revokes the session, clears the cookie, and returns `204`

#### Scenario: Unknown session logs out
- **GIVEN** no valid refresh session can be resolved
- **WHEN** logout is requested from an allowed origin
- **THEN** the API still clears the cookie and returns `204`

#### Scenario: Logout origin is untrusted
- **GIVEN** a browser sends logout with an untrusted Origin
- **WHEN** the request is validated
- **THEN** the API returns `403 permission_denied` without changing a valid session

### Requirement: Authentication rate limiting
Registration and login SHALL enforce independently configured request limits through
a deterministic, injected limiter and SHALL return `429 rate_limited` when a limit
is exceeded.

#### Scenario: Registration limit is exceeded
- **GIVEN** a client has exhausted the configured registration allowance
- **WHEN** another registration is attempted inside the window
- **THEN** the API returns `429 rate_limited` and creates no user

#### Scenario: Login limit is exceeded
- **GIVEN** a client has exhausted the configured login allowance
- **WHEN** another login is attempted inside the window
- **THEN** the API returns `429 rate_limited` and performs no successful authentication

### Requirement: Sensitive authentication data stays private
Password values, password hashes, access tokens, refresh credentials, refresh hashes,
and sensitive session metadata SHALL NOT appear in public user responses,
validation/domain error details, or application logs.

#### Scenario: Authentication flow is audited
- **GIVEN** successful and failed registration, login, refresh, identity, and logout requests
- **WHEN** responses and captured structured logs are inspected
- **THEN** none contains plaintext credentials, reusable tokens, password hashes, or refresh hashes

### Requirement: Authentication OpenAPI contract is complete
Every Phase 1 operation SHALL declare its summary, description, tags, response model,
status code, important error responses, and examples; Swagger, ReDoc, and the
versioned OpenAPI document SHALL expose the intended contracts.

#### Scenario: Developer inspects Swagger
- **GIVEN** documentation is enabled
- **WHEN** a developer opens `/docs`
- **THEN** all Phase 1 auth operations and the OAuth2 password flow are present and documented

#### Scenario: Frontend contract is generated
- **GIVEN** the Phase 1 application is running
- **WHEN** the documented frontend API-generation command runs
- **THEN** the committed TypeScript schema is regenerated without unexplained drift
