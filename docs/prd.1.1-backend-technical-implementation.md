# PRD 1.1 — پیاده‌سازی فنی Backend

## وضعیت سند

- نوع: Product Requirements Document فنی
- نسخه: 1.1
- تاریخ: 2026-07-29
- مالک: Backend/Product Engineering
- پشته: FastAPI + SQLAlchemy 2 Async + SQLite + Alembic
- مرجع‌ها: `AGENTS.md`, `docs/architecture.md`, `docs/engineering-rules.md`, `docs/use-cases.md`

## مسئله و هدف

محصول به یک API امن، مستند و type-safe نیاز دارد که مدیریت هویت، Workspace، Project، Task و Collaboration را برای UI فارسی فراهم کند. Backend باید منبع حقیقت Permission، ordering، completion و metrics باشد و ضمن استفاده از SQLite در MVP، به PostgreSQL قابل مهاجرت بماند.

هدف نهایی: همهٔ مسیرهای بحرانی از Register تا ساخت Workspace/Project/Task، Move، Collaboration و Dashboard از REST API و Swagger قابل اجرا و با تست خودکار قابل اثبات باشند.

## اهداف قابل اندازه‌گیری

- تمام Endpointها زیر `/api/v1` و در OpenAPI/Swagger قابل مشاهده‌اند.
- تمام Entityهای اصلی UUID، Constraint و Migration قابل تکرار دارند.
- هر Endpoint محافظت‌شده حداقل تست success، `401`, `403`, validation و not-found/conflict متناسب دارد.
- Business logic در Service و Query در Repository باقی می‌ماند.
- Move Task اتمیک، versioned و پس از Refresh پایدار است.
- Dashboard metricها با fixture database تطابق دارند.
- Quality Gate شامل Ruff، MyPy و Pytest بدون خطا است.

## خارج از Scope 1.1

WebSocket/SSE، worker جدا، email/push واقعی، SSO/LDAP، billing، webhook/public API key، automation builder، advanced time tracking، PostgreSQL production provisioning و S3 واقعی.

## معماری و ساختار

```text
backend/app/
  main.py
  api/deps.py, error_handlers.py, v1/router.py, v1/endpoints/
  core/config.py, database.py, security.py, permissions.py, logging.py
  models/ schemas/ repositories/ services/
  storage/base.py, storage/local.py
  jobs/generate_due_notifications.py
  seed.py
backend/migrations/
backend/tests/unit/
backend/tests/integration/
```

Dependency flow: API → Service → Repository → SQLAlchemy/DB. Service می‌تواند Storage، Notification و Activity را orchestration کند. Repository نباید Permission business decision بگیرد.

## نیازمندی‌های عملکردی

### BE-FR-01 Application foundation

- Config با `pydantic-settings` و Environment validation
- Async engine/session با SQLAlchemy 2
- Health endpoint و startup/shutdown امن
- CORS allowlist، request ID، structured logging و error handler مرکزی
- Swagger `/docs`، ReDoc `/redoc` و OpenAPI `/api/v1/openapi.json`
- Docs در Production با Environment قابل غیرفعال‌سازی

پذیرش: App روی port 8000 اجرا، health پاسخ و Schema معتبر تولید شود؛ Secret پیش‌فرض Production پذیرفته نشود.

### BE-FR-02 Identity و Session

Modelها: User و RefreshSession.

Endpointها:

```text
POST /auth/register
POST /auth/token
POST /auth/refresh
POST /auth/logout
GET  /auth/me
GET/PATCH /users/me
POST/DELETE /users/me/avatar
```

قواعد:

- Email lowercase/normalize و unique
- Password حداقل 10 کاراکتر، Argon2، generic credential error و dummy verify
- Access JWT برابر 30 دقیقه
- Refresh برابر 7 روز، Cookie `HttpOnly` و Session revocable
- Refresh rotation/revocation و Logout کامل
- Rate limit برای register/login
- OAuth2 Password Flow برای Swagger؛ `/auth/token` form-urlencoded

پذیرش: register/login/me/refresh/logout و expired/revoked token تست شوند؛ Hash هرگز قابل بازگردانی یا log نباشد.

### BE-FR-03 Workspace، Invitation و RBAC

Modelها: Workspace، WorkspaceMember، WorkspaceInvitation.

Endpointها:

```text
GET/POST /workspaces
GET/PATCH /workspaces/{workspace_id}
POST /workspaces/{workspace_id}/archive|restore
DELETE /workspaces/{workspace_id}
GET/POST /workspaces/{workspace_id}/members
PATCH/DELETE /workspaces/{workspace_id}/members/{user_id}
GET/POST /workspaces/{workspace_id}/invitations
DELETE /workspaces/{workspace_id}/invitations/{invitation_id}
POST /invitations/{token}/accept
```

Roleها: Owner، Admin، Project Manager، Member مطابق ماتریس `docs/architecture.md`.

پذیرش: ایجاد Workspace و Owner اتمیک؛ عضو موجود مستقیم، ناموجود Invitation؛ duplicate برابر `409`؛ Member role change برابر `403`؛ فقط Owner حذف/انتقال مالکیت.

### BE-FR-04 Project و Board columns

Modelها: Project، ProjectMember، BoardColumn.

Endpointها:

```text
GET/POST /workspaces/{workspace_id}/projects
GET/PATCH /projects/{project_id}
POST /projects/{project_id}/archive|restore
GET/POST /projects/{project_id}/members
PATCH/DELETE /projects/{project_id}/members/{user_id}
GET/POST /projects/{project_id}/columns
PATCH /columns/{column_id}
POST /projects/{project_id}/columns/reorder
POST /columns/{column_id}/archive
```

پذیرش: ساخت Project، Project Manager و پنج ستون پیش‌فرض یک Transaction؛ Key در Workspace unique؛ فقط عضو Workspace می‌تواند عضو Project شود؛ access Project خصوصی تست شود.

### BE-FR-05 Task core

Modelها: Task، TaskAssignee، Label، TaskLabel.

Endpointهای اصلی:

```text
GET/POST /projects/{project_id}/tasks
GET/PATCH /tasks/{task_id}
POST /tasks/{task_id}/move|archive|restore
POST/DELETE /tasks/{task_id}/assignees[/{user_id}]
GET/POST /projects/{project_id}/labels
PATCH/DELETE /labels/{label_id}
POST/DELETE /tasks/{task_id}/labels[/{label_id}]
GET/POST /tasks/{task_id}/subtasks
```

Queryها: pagination، search، column، assignee، label، priority، due range، overdue، completed، parent و sort allowlist.

Move contract:

```json
{
  "target_column_id": "uuid",
  "target_index": 2,
  "version": 4
}
```

Move باید permission/version را بررسی، source/target positions را اتمیک بازنویسی، completion را sync، version را افزایش، Activity/Notification لازم را ثبت و Task نهایی را برگرداند.

پذیرش: create/edit/archive، filters/sort/pagination، assignment/label، overdue، Done sync، N+1 audit و `409 version_conflict`.

### BE-FR-06 Collaboration

Modelها: Checklist، ChecklistItem، Comment، Attachment، ActivityLog.

قابلیت‌ها:

- CRUD و reorder برای Checklist/item
- Subtask در همان Project با Assignee/Due مستقل
- Comment create/edit/delete با ownership/role
- Attachment multipart، 10MB، MIME allowlist، UUID filename و Permission download
- Activity timeline برای Workspace/Project/Task

پذیرش: checklist progress، comment permission، path traversal، unauthorized upload/download، large/unsupported file و physical cleanup تست شوند.

### BE-FR-07 Notification

Model Notification شامل type، title/body، entity/action URL، read_at و created_at.

Endpointها:

```text
GET /notifications
GET /notifications/unread-count
PATCH /notifications/{id}/read
POST /notifications/read-all
```

رویدادها: membership، assignment، comment، mention، due soon، overdue، event مهم task. Self-notification ممنوع و due reminder با logical key deduplicate می‌شود.

پذیرش: unread، mark/read-all، navigation metadata، dedupe و job `generate_due_notifications` تست شوند.

### BE-FR-08 Reporting

Endpointها:

```text
GET /dashboards/global
GET /projects/{project_id}/dashboard
GET /projects/{project_id}/overview
GET /projects/{project_id}/timeline
GET /projects/{project_id}/calendar
```

Global: active workspaces/projects، my open/completed/overdue/today/next-7-days، completion 30d و recent activity.

Project: total/open/completed، completion، overdue/due soon/unassigned، group by column/priority/assignee و recent activity.

پذیرش: aggregateها محدود و permission-scoped؛ timezone boundary روشن؛ total صفر error ایجاد نکند.

### BE-FR-09 Seed و Delivery

Seed idempotent شامل چهار Role نمونه، یک Workspace، دو Project و حداقل 20 Task متنوع با collaboration/activity/notification.

پذیرش: اجرای دوباره duplicate نسازد؛ رمز Demo فقط Development/README؛ Docker volume برای SQLite/uploads؛ migration و startup از صفر مستند.

## Data contract

Entityهای کامل و Constraintها در `docs/architecture.md` منبع پایدارند. Fieldهای حساس (`password_hash`, token hash، session metadata حساس) هرگز در Response عمومی نیستند. DateTimeها offset-aware UTC و Responseها ISO 8601 هستند.

## Error contract

Error codeهای پایه:

```text
validation_error, authentication_required, invalid_credentials,
token_expired, permission_denied, resource_not_found,
resource_conflict, version_conflict, invalid_operation,
file_too_large, unsupported_file_type, rate_limited, internal_error
```

Resource غیرقابل دسترس در صورت نیاز برای جلوگیری از enumeration می‌تواند `404` بدهد. `500` request ID دارد و جزئیات داخلی را افشا نمی‌کند.

## ترتیب تحویل

1. Foundation
2. Database/Auth
3. Workspace/RBAC
4. Project/default board
5. Task core
6. Board move contract
7. Collaboration
8. Views/reporting
9. Notification/profile support
10. Hardening/seed/delivery

## Test و Quality Gate

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

تست Integration از SQLite موقت با schema تازه یا rollback استفاده می‌کند و اجرای Alembic از zero تا head را نیز پوشش می‌دهد. هر فاز بدون Pass کامل، قابل Done نیست.

## ریسک‌ها و کنترل

- SQLite write contention: Transaction کوتاه، query محدود و مسیر PostgreSQL
- Permission drift: dependency مشترک + service enforcement + matrix tests
- Ordering conflict: optimistic version + atomic reorder + `409`
- OpenAPI drift: generated client و CI check
- Notification spam: stakeholder filter + self suppression + dedupe key
- File abuse: size/MIME/path/storage boundary + permission checks

## Definition of Done Backend 1.1

همهٔ Flowهای E2E از Swagger و تست خودکار قابل اجرا، Migration و Seed سالم، Permission audit بدون Critical issue، OpenAPI client قابل تولید، Quality Gate سبز و محدودیت‌های Production ثبت شده‌اند.

