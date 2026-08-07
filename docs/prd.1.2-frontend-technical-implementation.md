# PRD 1.2 — پیاده‌سازی فنی Frontend

## وضعیت سند

- نوع: Product Requirements Document فنی
- نسخه: 1.2
- تاریخ: 2026-07-29
- مالک: Frontend/Product Design Engineering
- پشته: Next.js App Router + TypeScript + Tailwind CSS + shadcn/ui
- مرجع‌ها: `AGENTS.md`, `docs/use-cases.md`, `docs/design-guidelines.md`, Backend PRD 1.1

## مسئله و هدف

Frontend باید API پیچیدهٔ مدیریت پروژه را به تجربه‌ای فارسی، RTL، سریع و قابل پیش‌بینی تبدیل کند. همان Task source باید Board، List، Timeline، Calendar، Overview و Dashboard را تغذیه کند و Authorization، loading/error states و conflictهای optimistic را درست نمایش دهد.

هدف نهایی: کاربر فارسی‌زبان روی Desktop و Mobile بتواند جریان Register تا همکاری روی Task و گزارش‌گیری را بدون Mock دائمی، با Keyboard و Theme روشن/تیره تکمیل کند.

## اهداف قابل اندازه‌گیری

- تمام Routeهای MVP پیاده‌سازی و به API واقعی متصل‌اند.
- Root دارای `lang="fa"` و `dir="rtl"` و تمام Portalها RTL هستند.
- Typeها از OpenAPI تولید می‌شوند و drift دستی ندارند.
- Board move optimistic، rollback و conflict recovery دارد.
- هر Page حالت Loading، Empty، Error، Permission و No Result متناسب دارد.
- مسیرهای بحرانی با Component test و Playwright E2E پوشش دارند.
- lint، test، build و e2e بدون خطا هستند.

## خارج از Scope 1.2

Native mobile، offline-first، real-time multi-user cursor/edit، advanced Gantt dependency، bulk edit کامل، rich text editor، automation builder و marketplace.

## معماری Frontend

```text
frontend/src/
  app/
    layout.tsx, page.tsx
    (auth)/login,register
    (app)/app/
      page.tsx, notifications/, settings/profile/
      w/[workspaceId]/
        page.tsx, members/, settings/
        p/[projectId]/
          layout.tsx
          overview/, board/, list/, timeline/, calendar/
          dashboard/, members/, settings/
  components/ui|layout|workspace|project|board|task|dashboard/
  features/auth|workspaces|projects|tasks|notifications/
  lib/api|auth|dates|permissions|query-client.ts|utils.ts
  hooks/ providers/ messages/fa.ts types/
```

Server Components برای layout/shell/metadata/loading boundary و rendering غیرتعاملی. Client Components فقط برای form، Query hook، DnD، dialog/sheet، calendar، charts، notifications و local interaction.

State:

- Server state: TanStack Query
- Form: React Hook Form
- Validation: Zod
- URL: search params
- UI local: React state
- Auth access: in-memory provider؛ refresh در wrapper متمرکز

## نیازمندی‌های عملکردی

### FE-FR-01 Foundation و Design system

- Next.js App Router، TypeScript strict، Tailwind و shadcn/ui RTL
- Vazirmatn یا fallback مصوب؛ Light/Dark با semantic token
- App shell شامل Sidebar، Mobile Sheet، Topbar، Workspace switcher، Notification Bell، Breadcrumb و User menu
- Error boundary، loading skeleton، Sonner و providerهای Query/Auth/Theme
- localization مرکزی `messages/fa.ts` و digit normalization

پذیرش: صفحهٔ پایه روی 3000، RTL واقعی، theme persistence، responsive shell، keyboard navigation و بدون hydration error.

### FE-FR-02 Auth و Session UX

Routeها: `/`, `/login`, `/register`.

- Form با RHF/Zod و error فارسی
- Access token فقط Memory
- bootstrap session از refresh؛ تنها یک retry برای `401`
- redirect امن به `/app` و guard برای route خصوصی
- Logout پاک‌کردن auth/query state

پذیرش: validation، invalid credentials، expired token/refresh، reload persistence و logout E2E.

### FE-FR-03 Global Dashboard و Workspace

Routeها:

```text
/app
/app/w/[workspaceId]
/app/w/[workspaceId]/members
/app/w/[workspaceId]/settings
```

- Global metrics و recent activity
- Workspace cards/switcher، create/edit/archive متناسب با permission
- Member table، role select و invite dialog
- empty state برای نخستین Workspace/Project

پذیرش: permission controls فقط برای مجازها، API `403` نیز map شود؛ create workspace redirect و cache update صحیح.

### FE-FR-04 Project shell و Overview

Routeها:

```text
/app/w/[workspaceId]/p/[projectId]/overview
/members
/settings
```

- Project tabs و header مشترک
- status، dates، progress، counts، members، due soon و recent activity
- create/edit project، membership management و archived state

پذیرش: project create به Overview، پنج ستون از API، private access state و data واقعی.

### FE-FR-05 Board

Route: `/board`.

- ستون‌ها، add task composer، column menu/reorder/collapse/WIP
- Task card با title و metadata ضروری
- Search/filter: mine، assignee، label، priority
- DnD با snapshot → optimistic → API → sync؛ rollback و `409` refetch
- horizontal responsive layout و Keyboard DnD

پذیرش: move داخل/بین ستون، persistence پس از Refresh، RTL pointer behavior، keyboard alternative، network rollback و conflict message.

### FE-FR-06 Task detail

Task detail با query param یا intercepting route و Refresh/Share persistence.

- inline title/description
- assignee، label، priority، date range و column pickers
- checklist/subtask/comment/attachment/activity
- archive و copy link
- permission/read-only state

پذیرش: optimistic mutationها و error mapping؛ upload progress/validation؛ comment/checklist flow؛ focus management Sheet؛ URL close/open درست.

### FE-FR-07 List، Timeline و Calendar

- List: responsive table، pagination، search/sort/filter، row detail و quick edit محدود
- Timeline: day/week، task bars، group، zoom، no-date bucket، overdue و read-only MVP
- Calendar: month، optional week، due-date task، create from day و filter
- Filter state مشترک و URL قابل Share

پذیرش: همه از Task API مشترک، timezone/Persian display صحیح، empty/loading/error و permission states، no calculation از date string فارسی.

### FE-FR-08 Dashboardها

Project Dashboard:

- metric cards
- status donut/bar
- priority و workload bar
- overdue/upcoming/recent activity
- line chart فقط با دادهٔ زمانی معنی‌دار

Global Dashboard مطابق metrics Backend.

پذیرش: requestهای مستقل موازی، chart responsive/lazy و دارای text summary؛ total صفر درست.

### FE-FR-09 Notification و Profile

Routeها:

```text
/app/notifications
/app/settings/profile
```

- Poll هر 30 ثانیه در tab فعال، focus refetch و post-mutation refresh
- bell/unread/dropdown/page، mark one/all و entity navigation
- profile name/avatar/timezone و logout

پذیرش: badge sync، empty state، deep link، profile persistence، avatar errors و auth state cleanup.

## قرارداد API Client

OpenAPI از Backend مبنا است:

```json
{
  "scripts": {
    "generate:api": "openapi-typescript http://127.0.0.1:8000/api/v1/openapi.json -o src/lib/api/schema.d.ts"
  }
}
```

`openapi-fetch` wrapper باید:

- base URL از Environment
- Authorization header
- refresh single-flight و یک retry
- Error envelope parsing
- request cancellation در صورت نیاز
- بدون type assertion گسترده

را فراهم کند.

Query keyهای پایه:

```ts
["me"]
["workspaces"]
["workspace", workspaceId]
["workspace-members", workspaceId]
["projects", workspaceId, filters]
["project", projectId]
["columns", projectId]
["tasks", projectId, filters]
["task", taskId]
["notifications", filters]
["global-dashboard"]
["project-dashboard", projectId]
```

## UX error mapping

| API code | پیام فارسی |
|---|---|
| invalid_credentials | ایمیل یا رمز عبور صحیح نیست. |
| authentication_required | برای ادامه وارد حساب شوید. |
| token_expired | نشست شما منقضی شده است. دوباره وارد شوید. |
| permission_denied | اجازه انجام این عملیات را ندارید. |
| resource_not_found | مورد موردنظر پیدا نشد. |
| resource_conflict | این مورد با دادهٔ موجود تداخل دارد. |
| version_conflict | اطلاعات تغییر کرده است؛ صفحه به‌روزرسانی شد. |
| file_too_large | حجم فایل بیشتر از حد مجاز است. |
| unsupported_file_type | نوع این فایل پشتیبانی نمی‌شود. |
| rate_limited | درخواست‌های زیادی ارسال شده است. کمی بعد تلاش کنید. |
| internal_error | خطایی رخ داد. دوباره تلاش کنید. |

## کارایی

- جلوگیری از Client waterfall و fetch موازی Dashboard
- dynamic import برای chart/timeline سنگین
- direct imports و محدودکردن Recharts به Dashboard
- `next/image` برای Avatar
- Board card کوچک و memoization فقط پس از مشاهدهٔ نیاز
- stale time راهنما: me 5m، workspace 2m، board 15–30s، notifications 30s
- pagination/column limits در MVP؛ virtualization فاز بعد

## دسترس‌پذیری

- semantic landmark/header/nav/main
- focus visible، skip link و focus restoration
- form label/error association
- icon-only accessible name
- dialog trap و escape behavior
- keyboard DnD و alternative menu move
- chart text summary
- reduced motion و contrast در هر Theme

## Test plan

Component/integration:

- login/register validation
- workspace/project forms
- permission-based rendering
- board columns/task card و optimistic rollback
- task detail interactions
- filter URL state
- API error mapping و refresh single-flight
- notification badge
- loading/empty/error/permission/RTL

E2E: سناریوی کامل `docs/use-cases.md` روی Chromium، همراه یک Negative RBAC flow.

Quality Gate:

```bash
pnpm lint
pnpm test
pnpm build
pnpm e2e
```

## ترتیب تحویل

1. Foundation/RTL/design system
2. Auth/session
3. Workspace/RBAC UI
4. Project shell/overview
5. Task core/detail
6. Board/DnD
7. Collaboration
8. List/Timeline/Calendar/Dashboard
9. Notifications/Profile
10. Accessibility/performance/E2E hardening

## ماتریس پوشش اجباری Backend PRD 1.1

هیچ Endpoint محصولی که در Backend PRD 1.1 آماده است نباید بدون مسیر قابل استفاده در Frontend باقی بماند. ترتیب اتصال زیر بخشی از Scope نسخه 1.2 است:

| ترتیب | دامنه Frontend | قراردادهای Backend اجباری |
|---|---|---|
| 1 | ثبت‌نام، ورود، Guard و نشست | `auth/register`, `auth/token`, `auth/refresh`, `auth/logout`, `auth/me` |
| 2 | Workspace و RBAC | Workspace CRUD/archive/restore، members/roles، invitations create/list/revoke/accept |
| 3 | Project | Project CRUD/archive/restore، members/roles، columns CRUD/reorder/archive |
| 4 | Task | Task create/read/update/move/archive/restore، subtask، labels و assignees |
| 5 | همکاری | comments، checklists/items/reorder، attachments و activity |
| 6 | نماها | task list مشترک، timeline، calendar و project activity |
| 7 | گزارش | global dashboard و project dashboard |
| 8 | اعلان | list، unread count، mark one/all و deep-link |
| 9 | پروفایل | name، timezone، avatar upload/delete و هویت به‌روزشده |

### الزام Permission-aware UI

- نقش جاری از عضویت Workspace/Project استخراج می‌شود؛ کنترل‌های write/archive/member management فقط برای نقش مجاز render یا enable می‌شوند.
- پنهان‌کردن کنترل جایگزین enforce شدن Permission در Backend نیست و پاسخ `403` همیشه به state فارسی دسترسی محدود map می‌شود.
- تمام مسیرهای خصوصی تا پایان bootstrap refresh در حالت guard-loading می‌مانند و در نبود نشست به صفحه ورود بازمی‌گردند.
- URL و انتخاب Workspace/Project/View در History مرورگر ثبت می‌شود تا Refresh و Back/Forward رفتار پایدار داشته باشند.

## جهت بصری مرجع Trello

- پوستهٔ تیرهٔ متراکم با topbar جست‌وجو/ساخت، sidebar فضاهای کاری و canvas مستقل پروژه.
- Board افقی با listهای باریک، ارتفاع مستقل و composer ثابت در پایین؛ cardها metadata فشرده، label رنگی، تاریخ، checklist و assignee دارند.
- Task detail روی Desktop به dialog دو ستونه تبدیل می‌شود: محتوا و فیلدها در بخش اصلی، comment/activity در پنل کناری؛ روی Mobile به sheet تمام‌صفحه می‌رود.
- شباهت در hierarchy، density و affordance است؛ برند، رنگ، متن و RTL محصول مستقل باقی می‌مانند.

## ریسک‌ها و کنترل

- RTL library gaps: test portal، calendar و DnD در ابتدای هر component
- auth race: refresh single-flight و bounded retry
- stale optimistic state: server response sync، snapshot rollback و version conflict
- bundle growth: server/client boundary، lazy chart و import audit
- duplicate API types: generated schema only
- inaccessible DnD: keyboard sensor و explicit move menu

## Definition of Done Frontend 1.2

تمام routeها و flowهای MVP به Backend واقعی متصل، RTL/Theme/Mobile/Keyboard قابل استفاده، API client sync، critical E2E سبز، هیچ Critical mock/TODO باقی نمانده و Quality Gate کامل پاس شده است.
