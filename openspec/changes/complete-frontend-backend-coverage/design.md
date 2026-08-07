## Architecture

The existing authenticated request wrapper remains the single transport boundary. Binary downloads use the same bearer/refresh behavior and return object URLs managed by React effects. Deep links enter through App Router pages and converge on the existing session bootstrap before executing invitation or entity navigation.

## Backend read-contract additions

- Workspace listing accepts `include_archived=false` and retains membership scoping.
- Workspace/project member responses embed a minimal public user identity loaded eagerly by repositories.
- `GET /api/v1/auth/profile/avatar` streams only the current authenticated user's stored avatar.

## Interaction decisions

- Reordering uses explicit up/down keyboard controls; board task movement additionally supports pointer drag/drop and retains the select alternative.
- Archived resources are shown behind an explicit toggle and restoration invalidates active and archived queries.
- Permanent workspace deletion requires typed-name confirmation and is owner-only.
- Timeline offsets and widths derive from UTC task dates clamped to the requested visible range.
- Every mutation displays a normalized error and keeps destructive actions pending-disabled.

## Validation

Contract tests cover new backend fields and authorization. Component tests cover date positioning and route/deep-link helpers. Playwright covers invitation acceptance, management, board/detail collaboration, views, notification/profile and negative route/session behavior on desktop and mobile.
