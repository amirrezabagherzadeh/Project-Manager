# سامانهٔ مدیریت پروژهٔ فارسی

این مخزن یک API مستقل FastAPI و یک Web App مستقل Next.js دارد. Backend تا پایان
فاز 4 اکنون Database async، احراز هویت کامل، Workspace/RBAC، Project/Board
foundation و Task Core شامل Task، زیروظیفه، Label، Assignee، آرشیو و Query امن را
ارائه می‌کند؛ Move اتمیک/versioned Board نیز آماده است و Collaboration در فازهای
بعدی می‌آید.

## نسخه‌ها و پیش‌نیازها

- `uv` 0.11.26 یا جدیدتر؛ Python 3.12 را در صورت نیاز مدیریت می‌کند
- Python 3.12 (در اجرای تأییدشده: CPython 3.12.13 تحت مدیریت `uv`)
- Node.js 20.9 یا جدیدتر (در اجرای تأییدشده: 24.13.1)
- pnpm 10.30.1، مطابق `packageManager` در `frontend/package.json`
- OpenSpec 1.7.0
- Docker و Docker Compose فقط برای مسیر اختیاری Container

Backend و Frontend ریشهٔ Dependency مستقل دارند. Secret، فایل `.env` واقعی، Database محلی و Upload نباید commit شوند.

## اجرای صفر تا صد محلی

### Backend روی پورت 8000

PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
Set-Location backend
$env:PYTHONUTF8 = "1"
uv sync
New-Item -ItemType Directory -Force storage
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Unix-like shell:

```bash
cp backend/.env.example backend/.env
cd backend
uv sync
mkdir -p storage
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

پس از شروع:

- Health: <http://127.0.0.1:8000/health>
- Swagger: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI: <http://127.0.0.1:8000/api/v1/openapi.json>

در Windowsهایی که Console از UTF-8 استفاده نمی‌کند، `PYTHONUTF8=1` برای خروجی Unicode ابزار FastAPI لازم است. برنامه Secret پیش‌فرض Production ندارد و در `APP_ENVIRONMENT=production` بدون `APP_SECRET_KEY` شروع نمی‌شود. مستندات در Production نمایش داده نمی‌شوند.

فایل `.env` Development می‌تواند از مقدار ناامن محلی پیش‌فرض استفاده کند؛ در
Production باید `APP_SECRET_KEY` یکتا و حداقل 32 کاراکتر و
`APP_REFRESH_COOKIE_SECURE=true` باشد. Schema در Startup ساخته نمی‌شود؛
`alembic upgrade head` پیش‌نیاز Endpointهای Auth و Workspace است.

### Frontend روی پورت 3000

در Terminal جدا:

PowerShell:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
Set-Location frontend
pnpm install
pnpm dev
```

Unix-like shell:

```bash
cp frontend/.env.example frontend/.env.local
cd frontend
pnpm install
pnpm dev
```

صفحه در <http://127.0.0.1:3000> فارسی و RTL است. Navigation دسکتاپ از سمت راست و Navigation موبایل به‌شکل Sheet دسترس‌پذیر ارائه می‌شود.

## Quality Gate

Backend:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

Frontend:

```bash
cd frontend
pnpm lint
pnpm test
pnpm build
pnpm e2e
```

Playwright به Chromium نیاز دارد. نصب معمول:

```bash
cd frontend
pnpm exec playwright install chromium
```

اگر CDN مرورگر در منطقه در دسترس نباشد، تنظیم فعلی از Chrome نصب‌شدهٔ سیستم با `channel: "chrome"` استفاده می‌کند.

OpenSpec:

```bash
openspec validate --all --strict
```

Makefile در محیط‌های Unix-like میان‌برهای `backend-dev`, `backend-quality`, `frontend-dev`, `frontend-quality`, `generate-api` و `quality` را به ریشهٔ درست هر برنامه واگذار می‌کند. فرمان‌های Native بالا مرجع Windows هستند.

## قرارداد OpenAPI

Backend باید در حال اجرا باشد:

```bash
cd frontend
pnpm generate:api
```

این فرمان Schema را از `http://127.0.0.1:8000/api/v1/openapi.json` به `frontend/src/lib/api/schema.d.ts` می‌نویسد. فایل تولیدشده commit می‌شود تا Contract فاز جاری مشخص باشد؛ ویرایش دستی ممنوع است و بازتولید باید بدون Drift توضیح‌نداده باقی بماند.

## آزمودن Auth در Swagger یا Postman

Endpointهای فاز 1:

```text
POST /api/v1/auth/register
POST /api/v1/auth/token
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Swagger:

1. ابتدا `POST /api/v1/auth/register` را با `name`, `email`, `password` اجرا کنید.
2. روی **Authorize** بزنید؛ Email را در `username` و Password را در `password`
   وارد کنید. Swagger درخواست form-urlencoded را به `/api/v1/auth/token` می‌فرستد.
3. `GET /api/v1/auth/me` را اجرا کنید.
4. مرورگر Refresh Cookie از نوع `HttpOnly` را نگه می‌دارد؛
   `/auth/refresh` آن را rotate و `/auth/logout` آن را revoke/clear می‌کند.

Postman:

1. Register را با Body از نوع JSON اجرا کنید.
2. Token را با Body از نوع `x-www-form-urlencoded` و فیلدهای `username` و
   `password` اجرا کنید.
3. `access_token` را به‌صورت Bearer Token برای `/auth/me` بفرستید.
4. Cookie jar را فعال نگه دارید تا Refresh/Logout مقدار `ppm_refresh` را ارسال
   کنند. Header `Origin` اختیاری است؛ اگر ارسال شود باید یکی از
   `APP_TRUSTED_ORIGINS` باشد.

Register نشست ایجاد نمی‌کند. Access Token سی دقیقه اعتبار دارد. Refresh credential
هفت‌روزه، opaque و فقط به‌شکل SHA-256 در Database ذخیره می‌شود؛ هر Refresh آن را
rotate می‌کند و Replay مقدار قبلی، replacement chain را revoke می‌کند.

## آزمودن Project و Board در Swagger یا Postman

Endpointهای فاز 3:

```text
POST   /api/v1/workspaces/{workspace_id}/projects
GET    /api/v1/workspaces/{workspace_id}/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
POST   /api/v1/projects/{project_id}/archive
POST   /api/v1/projects/{project_id}/restore
GET    /api/v1/projects/{project_id}/members
POST   /api/v1/projects/{project_id}/members
PATCH  /api/v1/projects/{project_id}/members/{member_id}
DELETE /api/v1/projects/{project_id}/members/{member_id}
GET    /api/v1/projects/{project_id}/columns
POST   /api/v1/projects/{project_id}/columns
PATCH  /api/v1/projects/{project_id}/columns/{column_id}
POST   /api/v1/projects/{project_id}/columns/{column_id}/archive
PUT    /api/v1/projects/{project_id}/columns/reorder
```

پس از Register، ساخت Workspace و **Authorize** در Swagger:

1. با `POST /workspaces/{id}/projects` یک Project بسازید؛ `key` باید در همان
   Workspace یکتا باشد و در پاسخ، سازنده یک عضویت `manager` و دقیقاً پنج ستون
   `backlog`, `todo`, `doing`, `review`, `done` می‌گیرد (فقط `done` با
   `is_done=true`).
2. Project خصوصی (`is_private=true`) فقط برای ProjectMember و OWNER/ADMIN
   Workspace قابل مشاهده است؛ کاربر workspace عضو پروژه‌نشده، safe-`404` می‌گیرد.
3. با `POST /projects/{id}/members` یک کاربر موجود در Workspace را با نقش
   `manager` یا `member` اضافه کنید؛ عضویت تکراری `409` برمی‌گرداند.
4. با `PUT /projects/{id}/columns/reorder` فهرست کامل شناسهٔ ستون‌های فعال را
   بفرستید تا موقعیت‌ها اتمیک بازنویسی شوند؛ فهرست ناقص یا ناهم‌خوانا `409`
   برمی‌گرداند.
5. ساخت/ویرایش/آرشیو ستون و مدیریت عضویت پروژه به OWNER/ADMIN/PROJECT_MANAGER
   Workspace یا `manager` پروژه نیاز دارد؛ MEMBER برای این عملیات `403` می‌گیرد.

در Postman، `access_token` را در Authorization از نوع Bearer Token بگذارید.
پارامترهای فهرست `page` و `page_size` با پیش‌فرض 20 و سقف 100 هستند.

## آزمودن Workspace و RBAC در Swagger یا Postman

Endpointهای فاز 2:

```text
POST   /api/v1/workspaces
GET    /api/v1/workspaces
GET    /api/v1/workspaces/{workspace_id}
PATCH  /api/v1/workspaces/{workspace_id}
DELETE /api/v1/workspaces/{workspace_id}
POST   /api/v1/workspaces/{workspace_id}/archive
POST   /api/v1/workspaces/{workspace_id}/restore
GET    /api/v1/workspaces/{workspace_id}/members
POST   /api/v1/workspaces/{workspace_id}/members
PATCH  /api/v1/workspaces/{workspace_id}/members/{member_id}
DELETE /api/v1/workspaces/{workspace_id}/members/{member_id}
GET    /api/v1/workspaces/{workspace_id}/invitations
POST   /api/v1/workspaces/{workspace_id}/invitations
POST   /api/v1/workspaces/{workspace_id}/invitations/{invitation_id}/revoke
POST   /api/v1/invitations/{token}/accept
```

پس از Register و **Authorize** در Swagger:

1. با `POST /workspaces` یک Workspace بسازید؛ سازنده دقیقاً یک عضویت `OWNER`
   می‌گیرد.
2. با `POST /workspaces/{id}/members` یک User موجود را از روی Email و با نقش
   `ADMIN`، `PROJECT_MANAGER` یا `MEMBER` اضافه کنید.
3. برای User عضو‌نشده، `POST /workspaces/{id}/invitations` را اجرا و مقدار
   یک‌بارنمایش `token` را نگه دارید. فقط SHA-256 آن در Database ذخیره می‌شود.
4. با حساب دارای Email دعوت‌شده Authorize و
   `POST /invitations/{token}/accept` را اجرا کنید.
5. تغییر نقش با PATCH عضو انجام می‌شود. تعیین نقش `OWNER` توسط Owner فعلی،
   مالکیت را اتمیک منتقل و Owner قبلی را `ADMIN` می‌کند.
6. `OWNER` و `ADMIN` می‌توانند ویرایش، آرشیو و بازیابی کنند؛ فقط `OWNER`
   می‌تواند حذف دائمی انجام دهد. `PROJECT_MANAGER` و `MEMBER` برای عملیات
   مدیریتی `403` و کاربر غیرعضو safe-`404` می‌گیرند.

در Postman، `access_token` را در Authorization از نوع Bearer Token بگذارید.
پارامترهای فهرست `page` و `page_size` هستند؛ پیش‌فرض اندازه صفحه 20 و سقف آن
100 است. پاسخ ساخت دعوت تنها محل نمایش token خام است و پاسخ‌های بعدی آن یا hash
را برنمی‌گردانند.

## Alembic، Migration و Seed

فازهای 1 تا 3 Revisionهای زیر را دارند:

```bash
cd backend
uv run alembic current
uv run alembic upgrade head
```

Head فعلی `20260729_0003` علاوه بر `users`، `refresh_sessions` و جدول‌های
Workspace/RBAC/Activity/Notification، جدول‌های `projects`، `project_members` و
`board_columns` را با Constraint/Index/FKهای صریح می‌سازد. `make migrate` همین
Upgrade را اجرا می‌کند. Seed هنوز متعلق به فاز 9 است.

Rollback فقط روی Database صریحاً disposable یا تأییدشده:

```bash
cd backend
uv run alembic downgrade 20260729_0002
```

این Downgrade همهٔ داده‌های Project/member/column را حذف و فاز 2 را نگه می‌دارد.
Downgrade تا `base` همهٔ داده‌ها را حذف می‌کند؛ پیش از هر Rollback روی دادهٔ
واقعی Backup و تأیید اپراتور لازم است.

## اجرای اختیاری با Container

```bash
docker compose run --rm backend uv run --no-dev alembic upgrade head
docker compose up --build
```

Compose باید Backend را روی 8000، Frontend را روی 3000 و Storage پایدار Backend را در Volume نام‌گذاری‌شده اجرا کند. این مسیر یک Baseline توسعه است و ادعای Production readiness ندارد.

در محیط تأیید فعلی WSL 2.7.11، Docker Engine/CLI 29.6.2 و Compose 5.3.1 با Linux container اجرا شدند. هر دو Image ساخته شدند، Backend به وضعیت `healthy` رسید، صفحهٔ Frontend پاسخ `200` داد و Volume نام‌گذاری‌شدهٔ Backend پس از Restart سرویس پایدار ماند.

## تنظیمات Auth فاز 1

- `APP_DATABASE_URL`: پیش‌فرض SQLite در `./storage/app.db`
- `APP_SECRET_KEY`: کلید امضای HS256؛ در Production یکتا و حداقل 32 کاراکتر
- `APP_ACCESS_TOKEN_EXPIRE_MINUTES`: پیش‌فرض 30
- `APP_REFRESH_TOKEN_EXPIRE_DAYS`: پیش‌فرض 7
- `APP_REFRESH_COOKIE_*`: name/path/domain/Secure/SameSite
- `APP_CORS_ORIGINS` و `APP_TRUSTED_ORIGINS`: allowlist صریح؛ wildcard ممنوع
- `APP_REGISTER_RATE_LIMIT_*` و `APP_LOGIN_RATE_LIMIT_*`: limit/window مستقل

## محدودیت‌های شناخته‌شده

- Rate limiter در فاز 1 درون Process است؛ با Restart پاک می‌شود و بین چند Worker
  مشترک نیست. Adapter آن برای جایگزینی آینده حفظ شده است.
- SQLite برای MVP و Transactionهای کوتاه مناسب است، اما Refresh هم‌زمان در مقیاس
  Production باید همراه مهاجرت PostgreSQL بازبینی شود.
- Invitation در فاز 2 از طریق پاسخ API تحویل می‌شود؛ ارسال واقعی Email هنوز
  پیاده‌سازی نشده و token خام فقط در پاسخ ساخت دعوت نمایش داده می‌شود.
- Activity و Notification فاز 2 به‌شکل durable ثبت می‌شوند، اما API عمومی Bell،
  mark-read و polling در فاز 8 اضافه می‌شود.
- HTTPS termination، secret manager و distributed rate limiting بخشی از این
  Repository نیستند و برای Production الزامی‌اند.
- Docs در Production غیرفعال است؛ `Secure` Cookie و Secret معتبر در Startup enforce
  می‌شوند.

- Task، Move، Collaboration، Project views و Profile/Avatar هنوز خارج از فاز 3
  هستند؛ Phase 3 تنها Project، membership و Board column foundation را ارائه
  می‌دهد.
- حذف دائمی Project در فاز 3 وجود ندارد؛ آرشیو/بازیابی primitives هستند و Taskها
  در فاز 4 به آن متصل می‌شوند.
- Registry آنلاین shadcn هنگام Bootstrap از این محیط Timeout شد؛ `components.json`، Tokenها و Componentهای موردنیاز در مخزن قرار گرفته و با lint، build، component test و E2E واقعی تأیید شده‌اند.

## سابقهٔ تأیید فاز 1

در 2026-07-29 این موارد تأیید شدند:

- Migration خالی → Head، بازرسی Constraint/Index/FK، Downgrade و Re-upgrade
- Register، OAuth2 Login، Me، Refresh rotation/replay revocation و Logout از تست
  Integration و HTTP واقعی روی port 8000
- پاسخ `200` برای Health، Swagger، ReDoc و OpenAPI
- تولید `schema.d.ts` با SHA-256 برابر
  `9D0F8B5BECE616D83B59CB7AF766E04053AB415D9BF3DCC51F0659E926E71369`
- تست‌های منفی Validation، Credential، Token، Origin، Rate limit، Rollback و
  Sensitive-field audit

## سابقهٔ تأیید فاز 9

در 2026-08-07 این موارد تأیید شدند:

- دستور `ppm-seed` فقط در development/test، با اجرای دوباره بدون duplicate
- Migration head → base → head روی Database جداگانه و audit فیلدهای حساس OpenAPI
- Ruff، MyPy و 138 تست Pytest موفق؛ Health و Swagger روی سرویس تازه پاسخ 200

## سابقهٔ تأیید فاز 8

در 2026-08-07 این موارد تأیید شدند:

- migration `20260807_0006` برای timezone و avatar metadata پروفایل با downgrade
- API و تست Profile، avatar با MIME-safe storage و پاکسازی فایل قدیمی، inbox
  Notification، unread/read/read-all و Dashboard سراسری visibility-scoped
- generator سررسید Task با dedupe key یکتا و اجرای idempotent
- Quality gate: Ruff، MyPy و 138 تست Pytest؛ قرارداد TypeScript از OpenAPI منبع
  روی پورت 8007 بازتولید شد

## سابقهٔ تأیید فاز 7

در 2026-08-07 این موارد تأیید شدند:

- Dashboard پروژه با metrics `total`، `completed`، `overdue`، `due_soon` و
  `unassigned`، بدون تقسیم بر صفر و با مجوز resource-level
- endpointهای timeline/calendar با بازهٔ UTC و pagination و activity محدود پروژه
- Quality gate: Ruff، MyPy و 137 تست Pytest؛ قرارداد TypeScript از OpenAPI منبع
  روی پورت 8005 بازتولید شد

## سابقهٔ تأیید فاز 6

در 2026-08-07 این موارد تأیید شدند:

- migration `20260807_0005` برای Checklist، ChecklistItem، Comment و Attachment
  با FK/Index و upgrade/downgrade/re-upgrade
- API چک‌لیست/آیتم با CRUD، reorder کامل و progress؛ Comment با مالکیت نویسنده یا
  manager؛ پیوست با upload/list/download/delete و timeline فعالیت Task
- Storage محلی خارج از public با filename تولیدشده، containment، allowlist MIME و
  سقف 10MB؛ مسیر traversal، MIME نامجاز، حجم بیش از حد و cleanup پوشش داده شده‌اند
- Quality gate: Ruff، MyPy، 136 تست Pytest، OpenSpec strict و تولید مجدد قرارداد
  TypeScript از OpenAPI منبع روی پورت 8004

## سابقهٔ تأیید فاز 3

در 2026-08-07 این موارد تأیید شدند:

- Migration خالی تا `20260729_0003`، بازرسی Constraint/Index/FK، Downgrade به
  فاز 2 و Re-upgrade
- جریان HTTP کامل Owner → Workspace → Project → default columns → member add →
  private Project `404` → column reorder → archive/restore
- آفرینش اتمیک Project با عضویت `manager` سازنده و پنج ستون پیش‌فرض،
  private-access backend، safe-`404`، duplicate key `409` و rollback تزریق‌شدهٔ
  Activity/Notification
- پاسخ `200` برای Health، Swagger، ReDoc و OpenAPI روی Uvicorn واقعی پورت 8000
- ماتریس مجوز OWNER/ADMIN/PROJECT_MANAGER/MEMBER برای ساخت، ویرایش، آرشیو،
  عضویت و ستون‌ها
- توليد قرارداد TypeScript فاز 3 با SHA-256 برابر
  `7FE939B0A75465F6044AC22F3104C76CCEECB4714F9853FE8A184802763D57BB`
  و نبود `password_hash`، `refresh_token` یا `token_hash`

## سابقهٔ تأیید فاز 2

در 2026-07-29 این موارد تأیید شدند:

- Migration خالی تا `20260729_0002`، بازرسی Constraint/Index/FK، Downgrade به
  فاز 1 و Re-upgrade
- جریان HTTP کامل Owner → Workspace → member/role → invitation/accept →
  forbidden Member action → ownership transfer → archive/restore
- ماتریس نقش‌های `OWNER`، `ADMIN`، `PROJECT_MANAGER` و `MEMBER`، safe-`404`
  برای غیرعضو و rollback تزریق‌شدهٔ Activity/Notification
- پاسخ `200` برای Health، Swagger، ReDoc و OpenAPI روی Uvicorn واقعی پورت 8000
- 96 تست Backend و Ruff lint/format و MyPy strict موفق
- تولید قرارداد TypeScript فاز 2 با SHA-256 برابر
  `DC70949DBBE4C4158A31029EA79A864CE585CC082D677293438F2C22A9487225`
  و نبود `password_hash`، `refresh_token` یا `token_hash`

## سابقهٔ تأیید فاز صفر

در 2026-07-29 این موارد روی Windows تأیید شدند:

- Backend: Ruff lint و format، MyPy strict و 4 تست Pytest بدون Warning
- Frontend: ESLint، 3 تست Vitest، Build تولید Next.js و 2 سناریوی Playwright روی Chrome سیستم
- Runtime: پاسخ `200` برای Health، Swagger، ReDoc، OpenAPI و صفحهٔ Production Frontend
- UI: `lang="fa"`، `dir="rtl"`، Desktop/Mobile، Keyboard، Theme persistence و نبود overflow افقی
- Contract: تولید تکرارپذیر `schema.d.ts` با SHA-256 برابر `5B774DE18DD819F71FC6622612E5A17D472217412672FB342642FB55A3ED40A5`
- Alembic: اجرای `uv run alembic heads` بدون ساخت Database
- Dependency audit: اجرای `uvx pip-audit` بدون آسیب‌پذیری شناخته‌شده؛ `pnpm audit` دو هشدار High برای `brace-expansion` گزارش می‌کند، اما نسخه‌های نصب‌شدهٔ نگه‌داری‌شده (`1.1.16`، `2.1.3` و `5.0.8`) همگی محدودیت طول اصلاحی Advisory را در کد خود دارند. این اختلاف Metadata ثبت شده و Override ناسازگار روی زنجیرهٔ ESLint اعمال نشده است.
- OpenSpec: اجرای موفق `openspec validate --all --strict`

- Container: ساخت موفق Imageهای Backend و Frontend، وضعیت `healthy` برای Backend، پاسخ `200` روی پورت‌های 8000 و 3000، اجرای Frontend با کاربر غیر Root و پایداری `backend-data` پس از Restart
