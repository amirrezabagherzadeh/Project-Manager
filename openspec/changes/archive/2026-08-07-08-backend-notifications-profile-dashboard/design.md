## Decisions

Reuse Notification persistence and local storage protections. Notification reads are
always user-scoped; dedupe keys enforce logical uniqueness. Profile fields are added
through a reversible migration. Global aggregates join only resources visible through
workspace membership.

## Risks

- [Notification leakage] Filter all reads and state mutations by current user.
- [Avatar abuse] Generated names, MIME/size validation and physical cleanup.
- [Duplicate due notifications] Unique logical dedupe keys and idempotent job.
