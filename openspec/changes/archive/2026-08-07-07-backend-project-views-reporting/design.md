## Context

Tasks, columns, assignees, and ActivityLog already provide the source records.

## Decisions

Views are query-based and scope every result through existing Task project access.
Calendar/timeline ranges use UTC and return bounded Task public data; aggregates
return zero-safe values. SQL grouping is preferred over per-task Python queries.

## Risks

- [IDOR] Reuse TaskService access before all reads.
- [N+1] Use aggregates/select-in relationships and add query-budget tests.
- [Timezone ambiguity] Document UTC range semantics in OpenAPI.
