# قواعد مهندسی

## هدف

این سند استانداردهای اجباری ساخت، تست، امنیت و تحویل سامانهٔ مدیریت پروژهٔ فارسی را تعریف می‌کند. اصل راهنما: تغییر کوچک، صریح، قابل تست و قابل مهاجرت.

## چرخهٔ توسعه

1. ابتدا Change فعال، PRD و سند معماری خوانده شود.
2. Featureها به‌ترتیب فازهای Foundation، Auth، RBAC، Projects، Tasks، Board، Collaboration، Views، Dashboard و Hardening پیاده‌سازی شوند.
3. هر تغییر رفتاری باید Requirement، Scenario، Task و Test داشته باشد.
4. قبل از رفتن به فاز بعد، Acceptance و Quality Gate فاز جاری کامل شود.
5. تغییرات نامرتبط، Refactor بزرگ و Dependency جدید وارد Scope نشوند.

## Backend

- Route Handler فقط Parse، Dependency Injection، Authentication، OpenAPI metadata، Status Code و Serialization را انجام می‌دهد.
- Service Layer مالک Business Rule، Permission نهایی، Transaction، Activity و Notification است.
- Repository Layer مالک Query، CRUD، Pagination، Filter و eager loading است.
- Modelها Constraint، Index و Relationship را تعریف می‌کنند؛ Schemaهای Pydantic فیلدهای Public/Private را جدا می‌کنند.
- عملیات مرکب زیر Atomic هستند:
  - Workspace + Owner Membership
  - Project + Manager + پنج ستون پیش‌فرض
  - Move Task + reorder + completion + Activity
  - Assignment + Notification
  - Accept Invitation + Membership
  - حذف metadata و cleanup فایل
- List endpoint نباید graph کامل Comments/Attachments را Load کند. Task detail می‌تواند دادهٔ کامل برگرداند.
- Pagination پیش‌فرض 20 و حداکثر 100 است.
- Sort فقط با allowlist انجام شود؛ نام Column از Client مستقیم وارد Query نشود.
- برای Relationshipها `selectinload` یا `joinedload` هدفمند و برای Dashboard Queryهای aggregate استفاده شود.

## Database

- تمام IDها UUID و تمام timestampها UTC هستند.
- SQLite انتخاب MVP است؛ از رفتارهای اختصاصی آن که مهاجرت به PostgreSQL را سخت می‌کند دوری شود.
- Foreign Key، Unique Constraint و Indexهای query-driven صریح باشند.
- تغییر Schema فقط با Alembic؛ Migration upgrade/downgrade و اجرای آن روی Database خالی تست شود.
- Seed idempotent باشد و فقط در Development رمز نمونه تعریف کند.
- Archive با `archived_at` برای Project/Task/Column مسیر پیش‌فرض حذف است.
- Task از `version` برای optimistic concurrency استفاده می‌کند.

## API و OpenAPI

- Prefix: `/api/v1`
- موفقیت Single: `{ "data": {...} }`
- موفقیت List: `{ "data": { "items": [], "page": 1, "page_size": 20, "total": 0 } }`
- خطا: `{ "error": { "code": "...", "message": "...", "details": null, "request_id": "..." } }`
- Statusهای اصلی: `200/201/204`, `400`, `401`, `403`, `404`, `409`, `413`, `415`, `422`, `429`, `500`
- هر Route باید `summary`، `description`، `response_model`، `status_code`، `tags`، Errorهای مهم و Example داشته باشد.
- Endpoint فقط وقتی کامل است که در Swagger دیده و با کاربر مجاز و غیرمجاز تست شود.
- OpenAPI در `/api/v1/openapi.json` منتشر شود و `openapi-typescript`/`openapi-fetch` Client را تولید کنند.
- CI باید drift بین Schema و Client تولیدشده را رد کند.

## Authentication و Authorization

- Access JWT کوتاه‌عمر 30 دقیقه و فقط در Memory Frontend.
- Refresh Token هفت‌روزه در Cookie امن `HttpOnly`، قابل rotation/revoke و دارای Session DB.
- Logout باید Session را revoke و Cookie را پاک کند.
- Password حداقل 10 کاراکتر و با Argon2 Hash شود.
- Login error عمومی، dummy verify برای Email ناموجود و rate limit برای Login/Register الزامی است.
- ترتیب Permission dependency: current user → workspace membership/role → project membership/management → task edit permission.
- جلوگیری از IDOR با Resource-level authorization و Negative permission test.

## Frontend

- Server Component برای shell، metadata، layout و initial rendering؛ Client Component فقط برای فرم، DnD، interactive overlay، Query hooks، Charts و local UI state.
- `"use client"` در بالاترین سطح Tree بدون ضرورت ممنوع است.
- Server state با TanStack Query، form state با React Hook Form، validation با Zod، URL state با search params و local state با React نگهداری شود.
- Global heavyweight state manager در MVP اضافه نشود.
- Mutation باید pending/error/success داشته باشد، cache را دقیق update/invalidate کند و پیام فارسی بدهد.
- DnD باید optimistic snapshot، rollback و مسیر `409 version_conflict` با refetch داشته باشد.
- Query keyها domain-first و پایدار باشند، مانند `["tasks", projectId, filters]`.
- Filter/Sort/Search در URL باقی بماند تا Refresh و Share حفظ شوند.
- تمام stringهای کاربرمحور در `messages/fa.ts` باشند؛ Code، Enum و API field انگلیسی بمانند.

## Security و File

- Secret، Token و Password هرگز commit یا log نشود.
- CORS با allowlist؛ wildcard همراه credential ممنوع.
- Cookie در Production: `Secure`, `HttpOnly` و `SameSite` مناسب.
- Structured logging همراه request ID؛ پاسخ 500 بدون stack trace.
- Description و Comment در MVP plain text یا sanitize‌شده.
- Upload: سقف پیش‌فرض 10MB، MIME allowlist، بررسی محتوا در حد لازم، نام ذخیره UUID، sanitize نام اصلی، ذخیره خارج web root و Download فقط پس از Permission.
- Path traversal، فایل بزرگ، MIME نامعتبر و Upload/Download غیرمجاز تست شوند.

## Test Strategy

- Backend unit: password، token، permission matrix، completion/overdue، reorder، notification dedupe، file validation
- Backend integration: auth، workspace، RBAC، project/default columns، task، assign/move، checklist/subtask/comment/file، dashboard، pagination/filter/sort و error paths
- Frontend: forms، permission UI، board/task detail، filters، error mapping، notifications و UI states
- E2E بحرانی: register/login → workspace → member → project → task → assign → drag to done → checklist → upload → dashboard → forbidden admin action → session persistence/logout
- Snapshot RTL محدود و هدفمند؛ Behavior test بر Snapshot اولویت دارد.

## کارایی و دسترس‌پذیری

- Dashboard fetchها موازی، waterfall کم و chart/timeline سنگین dynamic شوند.
- Recharts فقط در bundle داشبورد؛ Avatar با `next/image`.
- Query stale time راهنما: profile پنج دقیقه، workspaces دو دقیقه، board 15–30 ثانیه، notifications سی ثانیه.
- Keyboard navigation، visible focus، semantic controls، form label، focus trap، `aria-label`، contrast، DnD keyboard، chart summary و `prefers-reduced-motion` الزامی است.

