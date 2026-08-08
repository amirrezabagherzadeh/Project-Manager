# Changelog

همهٔ تغییرات مهم پروژه در این فایل ثبت می‌شوند. قالب بر مبنای Keep a Changelog است و نسخه‌گذاری پس از شروع انتشار از Semantic Versioning پیروی می‌کند.

## [Unreleased]

### Fixed

- ساخت سرویس ذخیره‌سازی فایل به‌صورت lazy انجام می‌شود تا endpointهای Comment،
  Checklist، Activity و Attachment list روی فایل‌سیستم فقط‌خواندنی Vercel با خطای
  `500` متوقف نشوند.

### Added

- Complete PRD 1.2 frontend program: registration/login/refresh/logout and identity,
  permission-aware workspace/project administration, Trello-style Board and task
  detail, collaboration, List/Timeline/Calendar, dashboards, notifications and profile.
- Typed authenticated API adapter covering the PRD 1.1 contract, single-flight refresh,
  generated OpenAPI schemas, responsive Persian RTL shell and desktop/mobile E2E flows.
- Development seed migration from reserved `demo@local.test` to valid
  `demo@example.com`, preserving the existing demo user and workspace.
- Frontend board foundation: Persian RTL Trello-style board connected to the
  existing REST/SQLite data flow, demo-session bootstrap, project bootstrap,
  task creation, optimistic task movement, and loading/error states.
- Backend فاز 9: seed توسعهٔ محافظت‌شده و idempotent، audit migration chain و
  delivery verification نهایی برای quality gates و OpenAPI
- Backend فاز 8 برای Profile نام/Timezone/Avatar، Notification inbox/read state،
  due-notification idempotent و Dashboard سراسری scope‌شده
- Backend فاز 7 برای Dashboard پروژه، metrics صفر-ایمن، overdue/due-soon/unassigned،
  timeline/calendar UTC و activity محدود با مجوز پروژه
- Backend فاز 6 برای Collaboration وظیفه: CRUD چک‌لیست/آیتم، reorder و progress،
  مالکیت Comment، پیوست multipart با دریافت/حذف مجاز و timeline فعالیت Task
- migration `20260807_0005`، storage محلی خارج از public با نام تولیدشده، سقف 10MB،
  allowlist MIME و حفاظت traversal؛ تست‌های integration و storage برای دسترسی و cleanup
- Backend فاز 5 برای Move اتمیک Board با قرارداد `target_column_id`/
  `target_index`/`version`، `409 version_conflict` و normalize شدن positionها
- همگام‌سازی `completed_at` با ستون Done، persistence پس از refresh و تست stale
  version، move بین ستون‌ها و reorder در یک تراکنش کوتاه
- Backend فاز 4 برای Task Core با Task، Label، TaskAssignee و TaskLabel، migration
  `20260807_0004`، UUID/UTC، FK/Constraint/Index و downgrade/re-upgrade قابل تکرار
- APIهای Task create/list/detail/update/archive/restore، زیروظیفه، assignee، label
  و CRUD برچسب با resource-level authorization، pagination، search و sort allowlist
- تست Integration فاز 4 برای `401`، safe-`404`، validation، Query امن، archive/
  restore، subtask، assignee و label conflict
- Backend فاز 3 برای Project/Board foundation با Project، ProjectMember و
  BoardColumn، کلید یکتای Workspace، private-project access و پنج ستون پیش‌فرض
- Alembic revision `20260729_0003` برای Project/member/column با UUID/UTC،
  Constraintها، Indexها و FKهای صریح و Downgrade به فاز 2
- ساخت اتمیک Project با عضویت `manager` سازنده، پنج ستون `backlog`/`todo`/
  `doing`/`review`/`done` (فقط `done` با `is_done=true`) و Activity در یک تراکنش
- CRUD/فهرست/آرشیو/بازیابی Project، مدیریت عضویت پروژه (manager/member)،
  ستون‌های Board با reorder اتمیک full-list و archive
- مجوز Resource-level برای Project با safe-`404` غیرعضو در Project خصوصی و
  `409` برای کلید/عضویت تکراری
- Activity و Notification پروژه‌محور اتمیک با self-notification suppression و
  rollback در شکست side effect
- تست‌های مدل، Migration، Repository، permission matrix، Service، API، OpenAPI،
  rollback و جریان کامل HTTP فاز 3؛ Quality Gate با 134 تست موفق
- قرارداد TypeScript فاز 3 با SHA-256
  `7FE939B0A75465F6044AC22F3104C76CCEECB4714F9853FE8A184802763D57BB`
- Backend فاز 2 برای Workspace/RBAC با نقش‌های `OWNER`، `ADMIN`,
  `PROJECT_MANAGER` و `MEMBER` و enforce شدن مجوز در Service/Resource scope
- Alembic revision `20260729_0002` برای Workspace، membership، invitation،
  Activity و Notification با UUID/UTC، Constraintها، Indexها و FKهای صریح
- API کامل ساخت/فهرست/مشاهده/ویرایش/آرشیو/بازیابی/حذف Workspace، مدیریت عضو،
  تغییر نقش، انتقال اتمیک مالکیت و pagination محدود
- دعوت امن با Email نرمال‌شده، token یک‌بارنمایش، ذخیرهٔ SHA-256، expiry/revoke/
  single-use acceptance و تطبیق Email کاربر جاری
- Activity و Notification اتمیک، rollback در شکست side effect، self-notification
  suppression و safe-`404` برای جلوگیری از enumeration میان Workspaceها
- تست‌های مدل، Migration، Repository، permission matrix، Service، API، OpenAPI،
  rollback و جریان کامل HTTP فاز 2؛ Quality Gate با 96 تست موفق
- قرارداد TypeScript فاز 2 با SHA-256
  `DC70949DBBE4C4158A31029EA79A864CE585CC082D677293438F2C22A9487225`
- Backend فاز 1 با SQLAlchemy 2 Async، Session درخواست‌محور، Foreign Key فعال
  SQLite، UUID/UTC convention و Transactionهای Service-owned
- Alembic revision `20260729_0001` برای `users` و `refresh_sessions` با
  upgrade/downgrade، Constraintها و Indexهای صریح
- `POST /api/v1/auth/register`، OAuth2 form login در `/auth/token`،
  `GET /auth/me`، Refresh rotation/replay revocation و Logout
- Password Argon2 با dummy verification، Access JWT سی‌دقیقه‌ای HS256 با
  `sub/iat/exp/jti` و Refresh opaque هفت‌روزه با ذخیرهٔ SHA-256
- Cookie امن و وابسته به Environment، allowlist مبدأ برای Refresh/Logout و
  rate limiter تزریق‌پذیر مستقل برای Register/Login
- تست‌های Unit/Integration/Migration/HTTP برای مسیرهای موفق، `401`، `403`،
  `409`، `422`، `429`، rollback، replay و عدم افشای فیلدهای حساس
- Quality Gate فاز 1: Ruff lint/format، MyPy روی 29 فایل و 71 تست Pytest موفق
- قرارداد TypeScript فاز 1 با پنج عملیات Auth و SHA-256
  `9D0F8B5BECE616D83B59CB7AF766E04053AB415D9BF3DCC51F0659E926E71369`
- پایهٔ قابل اجرای Backend با Python 3.12، FastAPI 0.140.13، Pydantic Settings، Request ID، Logging ساختاریافته و Error envelope امن
- مسیرهای `/health`، `/docs`، `/redoc` و `/api/v1/openapi.json` همراه Policy غیرفعال‌سازی مستندات در Production
- زیرساخت Alembic بدون Domain revision یا ایجاد Database در فاز صفر
- پایهٔ Frontend با Next.js 16.2.12، React 19.2.8، TypeScript strict، Tailwind CSS 4.3.3 و shadcn/ui RTL
- Shell فارسی RTL، پوستهٔ روشن/تیره، Navigation واکنش‌گرا و الگوهای Loading، Empty، Error و Permission
- Vitest/Testing Library، Playwright با Chrome سیستم و تولید Typeهای TypeScript از OpenAPI
- Dockerfileهای Backend/Frontend، Compose توسعه با Volume پایدار Backend، Makefile و راهنمای صفر تا اجرا
- تأیید Runtime فایل Compose با Build واقعی هر دو Image، Healthcheck موفق Backend، صفحهٔ Frontend و پایداری Volume پس از Restart
- حافظهٔ دائمی عامل‌ها در `AGENTS.md` و ارجاع مشترک Claude Code در `CLAUDE.md`
- اسناد مهندسی، معماری، Use Case و Design Guideline در `docs/`
- PRD فنی Backend نسخهٔ 1.1 و Frontend نسخهٔ 1.2
- OpenSpec 1.7.0 با integrationهای Codex و Claude Code
- پیکربندی OpenSpec برای تولید Proposal، Spec، Design و Task بر اساس PRDها و اسناد پروژه
- Change اولیهٔ OpenSpec برای Phase 0 شامل Proposal، سه Spec، Design و 21 Task قابل ردیابی
- نقشه‌راه OpenSpec با شناسهٔ `01-backend-prd` برای تحویل مرحله‌ای تمام Backend،
  شامل قرارداد تحویل، Design، Taskهای Gateشده و Master Prompt اجرای فازهای 1 تا 9
- Skillهای Next.js App Router، shadcn/ui، Tailwind CSS 4، FastAPI و SQLite برای Codex

### Planned

- فاز 6: Task Collaboration
- فاز 7: Project Views
- فاز 8: Global Dashboard، Notifications و Profile
- فاز 9: Hardening و Delivery

### Known limitations

- Move اتمیک/versioned، Collaboration، Project views و Profile/Avatar هنوز خارج از
  فاز 4 هستند؛ فاز 4 Task Core را بدون تغییر column/reorder ارائه می‌دهد.
- حذف دائمی Project در فاز 3 وجود ندارد؛ آرشیو/بازیابی primitives هستند و
  Taskهای فاز 4 به Board columnها متصل می‌شوند.
- ارسال Email دعوت در فاز 2 وجود ندارد؛ token خام فقط یک بار در پاسخ ساخت دعوت
  برمی‌گردد.
- API عمومی Notification polling/mark-read در فاز 8 اضافه می‌شود؛ فاز 2 تنها
  persistence لازم برای side effectهای Workspace را فراهم می‌کند.
- Rate limiter فاز 1 تک‌Process و غیرمشترک میان Workerها است و با Restart پاک می‌شود.
- SQLite در MVP استفاده می‌شود؛ رقابت Refresh هم‌زمان در استقرار چند Worker باید
  همراه مهاجرت PostgreSQL و limiter توزیع‌شده بازبینی شود.
- Production به secret یکتای حداقل 32 کاراکتر، HTTPS termination و Secure Cookie
  نیاز دارد؛ Docs در Production غیرفعال است.
- CDN رسمی Playwright در منطقهٔ فعلی `403` می‌دهد؛ E2E با Chrome نصب‌شدهٔ سیستم اجرا و تأیید شده است.
- Registry آنلاین shadcn/ui در زمان Bootstrap Timeout شد؛ پیکربندی و Componentهای محلی با lint، build، component test و E2E تأیید شدند.
- `pnpm audit` برای نسخه‌های نگه‌داری‌شدهٔ `brace-expansion` در زنجیرهٔ ابزار توسعه دو هشدار Metadata گزارش می‌کند؛ نسخه‌های نصب‌شده دارای همان محدودیت طول اصلاحی Advisory هستند و Backend audit بدون یافته است.
