## Decisions

The seed rejects production, uses canonical services for idempotent records, and
never contains real credentials. Final verification uses an empty disposable DB,
strict static gates, OpenAPI generation, and a fresh local Swagger process.

## Risks

- [Production data mutation] Require development/test environment.
- [Schema drift] Validate clean upgrade, downgrade and re-upgrade.
- [Sensitive output] Audit generated OpenAPI and public schemas.
