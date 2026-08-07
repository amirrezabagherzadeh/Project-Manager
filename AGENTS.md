# راهنمای دائمی عامل‌های پروژه

این فایل حافظهٔ اجرایی بلندمدت پروژه است. هر عامل کدنویسی باید پیش از هر تغییر، این فایل و اسناد مرتبط در `docs/` را بخواند. منبع اولیهٔ تصمیم‌ها سند `CODEX_PLAN_PERSIAN_PROJECT_MANAGEMENT.md` بوده و تصمیم‌های تثبیت‌شده در اسناد زیر تفکیک شده‌اند.

## مأموریت محصول

ساخت یک وب‌اپلیکیشن حرفه‌ای مدیریت پروژه و وظیفه برای تیم‌های فارسی‌زبان با تجربه‌ای نزدیک به Trello، Asana و Jira؛ محصول از ابتدا فارسی، راست‌چین، دسترس‌پذیر، واکنش‌گرا و مناسب استفادهٔ روزمره طراحی می‌شود.

کاربر باید بتواند حساب و پروفایل خود را مدیریت کند، Workspace بسازد، عضو و Role تعریف کند، Project بسازد، Taskها را در Board جابه‌جا کند و همان داده را در نماهای List، Timeline، Calendar، Overview و Dashboard ببیند. Task از Assignee، Label، Priority، تاریخ، Subtask، Checklist، Comment، Attachment، Activity و Notification پشتیبانی می‌کند.

## اسناد مرجع و ترتیب اعتبار

1. تغییر فعال OpenSpec در `openspec/changes/<change-id>/`
2. PRDهای فنی:
   - `docs/prd.1.1-backend-technical-implementation.md`
   - `docs/prd.1.2-frontend-technical-implementation.md`
3. اسناد پایدار پروژه:
   - `docs/engineering-rules.md`
   - `docs/architecture.md`
   - `docs/use-cases.md`
   - `docs/design-guidelines.md`
4. این فایل
5. `CHANGELOG.md` برای تاریخچه، نه تعریف رفتار آینده

اگر اسناد تعارض داشتند، کار را متوقف نکنید: امن‌ترین تغییر کوچک را انتخاب کنید، تعارض را در Proposal یا گزارش پایان کار ثبت کنید و رفتار عمومی موجود را بدون مجوز تغییر ندهید.

## پشتهٔ قطعی

- Backend: Python 3.12، FastAPI، Pydantic v2، SQLAlchemy 2 Async، `aiosqlite`، Alembic، PyJWT، `pwdlib[argon2]`
- Frontend: Next.js App Router، React، TypeScript strict، Tailwind CSS، shadcn/ui، TanStack Query، React Hook Form، Zod
- تعامل: `@dnd-kit/react`، Recharts، Sonner، `next-themes`
- قرارداد: REST/JSON زیر `/api/v1` و تولید Typeهای Frontend از OpenAPI
- پایگاه دادهٔ MVP: SQLite؛ طراحی و Migrationها باید مسیر مهاجرت به PostgreSQL را باز نگه دارند.
- ذخیره‌سازی MVP: فایل محلی پشت `StorageService`؛ مسیر آینده S3-compatible
- Notification در MVP: Database + Polling؛ مسیر آینده WebSocket/SSE
- معماری نسخهٔ اول: Modular Monolith با Frontend و Backend مستقل

## قواعد غیرقابل مذاکره

- فازهای 0 تا 9 به‌ترتیب اجرا می‌شوند. تا معیار پذیرش و Quality Gate یک فاز پاس نشده، فاز بعدی شروع نشود.
- Business Logic داخل FastAPI Route Handler ممنوع است؛ API فقط ورودی، Dependency، Status و Serialization را مدیریت می‌کند.
- مجوزها همیشه در Backend و در سطح Resource enforce شوند؛ مخفی‌کردن کنترل UI کافی نیست.
- هیچ Password یا Secret خام ذخیره، log یا commit نشود.
- همهٔ زمان‌های Backend به UTC و ISO 8601 باشند؛ تبدیل Locale/Timezone در مرز نمایش انجام شود.
- همهٔ تغییرات Schema فقط با Alembic انجام شوند.
- Delete برای Project و Task در مسیر عادی به Archive ترجیح داده شود.
- Typeهای API در Frontend دستی تکثیر نشوند؛ از OpenAPI تولید شوند.
- Mock Data دائمی پس از آماده‌شدن Endpoint مجاز نیست.
- هر صفحه باید Loading، Empty، Error، Permission، Offline و حالت بدون نتیجه داشته باشد.
- متن کاربرمحور در Componentها hardcode نشود؛ Locale اصلی `fa-IR` است.
- هر Endpoint باید OpenAPI metadata، مدل Request/Response، Status Code، مثال و تست موفق/ناموفق داشته باشد.
- Dependency یا API جدید فقط پس از بررسی مستندات همان نسخه اضافه شود.

## روش اجرای تغییر

1. اسناد مرتبط و کد موجود را بخوانید.
2. برای Feature یا تغییر رفتاری، ابتدا با OpenSpec Proposal بسازید.
3. Requirementها و Scenarioها را به Use Case و Acceptance Criterion مرجع متصل کنید.
4. تغییر کوچک و دامنه‌محور انجام دهید؛ Public API را بی‌دلیل نشکنید.
5. Migration، OpenAPI client، تست و مستندات مرتبط را هم‌زمان به‌روز کنید.
6. Quality Gate همان فاز را اجرا کنید.
7. نتیجه و محدودیت شناخته‌شده را در `CHANGELOG.md` ثبت کنید.

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

OpenSpec و قرارداد:

```bash
openspec validate --all
cd frontend
pnpm generate:api
```

فقط فرمان‌های موجود در فاز جاری اجرا شوند. اگر برنامه هنوز Bootstrap نشده است، نبود فرمان را به‌عنوان وضعیت Foundation گزارش کنید، نه موفقیت تست.

## Definition of Done هر قابلیت

- Requirement و Scenario قابل ردیابی دارد.
- مجوز موفق، `401`، `403`، Validation و Not Found/Conflict تست شده‌اند.
- Swagger/OpenAPI صحیح و Frontend client همگام است.
- UI فارسی RTL، Responsive، Keyboard-accessible و دارای Stateهای الزامی است.
- Activity/Notification در صورت نیاز و بدون Spam ثبت می‌شود.
- Migration و Seed در صورت نیاز idempotent هستند.
- Quality Gate پاس شده و Changelog به‌روز است.

## Skill و مستندات

پیش از کار مرتبط، Skillهای Next.js، shadcn/ui و React best practices موجود در محیط را بخوانید. Skillهای Project-local در `.agents/skills/` یا مسیرهای Agent قرار می‌گیرند. Skill جایگزین Documentation رسمی نیست؛ برای APIهای متغیر از Context7/Documentation رسمی استفاده شود.

## OpenSpec

OpenSpec برای تبدیل PRD و اسناد `docs/` به Proposal، Specs، Design و Tasks استفاده می‌شود. `openspec/config.yaml` قواعد پروژه را به همهٔ Artifactها تزریق می‌کند. نام Change به شکل kebab-case و خروجی هر Task باید به Acceptance Criterion و تست متناظر وصل باشد.

