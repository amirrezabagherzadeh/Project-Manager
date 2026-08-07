# موارد کاربرد و جریان‌های کاربر

## Actorها

- Visitor: ثبت‌نام و ورود
- Member: کار روزانه روی Taskهای Projectهایی که عضو است
- Project Manager: مدیریت Project، Board و اعضای Project
- Workspace Admin: مدیریت Workspace و اعضا به‌جز Owner
- Workspace Owner: مالکیت، حذف و انتقال Ownership
- System: Reminder، Notification، Activity و محاسبهٔ Dashboard

## UC-01 ثبت‌نام و ورود

پیش‌شرط: کاربر Session معتبر ندارد.

جریان اصلی:

1. Visitor در `/register` نام، Email و Password را وارد می‌کند.
2. Client validation و سپس API validation اجرا می‌شود.
3. حساب ایجاد و کاربر وارد Login یا مستقیماً App می‌شود.
4. Login با form-urlencoded به `/auth/token`، Access Token و Refresh Cookie می‌گیرد.
5. `/auth/me` هویت را تأیید و `/app` باز می‌شود.
6. نخستین کاربر Empty State ساخت Workspace را می‌بیند.

مسیر جایگزین:

- Credential اشتباه پیام عمومی می‌دهد.
- Access منقضی یک Refresh خودکار دارد؛ شکست آن Session را پاک می‌کند.
- Logout RefreshSession را revoke می‌کند.

پذیرش: Password خام ذخیره نمی‌شود، Swagger Authorize کار می‌کند، expired/revoked token و `401` تست دارند.

## UC-02 ساخت Workspace

1. کاربر «ساخت فضای کاری» را انتخاب می‌کند.
2. نام و توضیح را وارد می‌کند.
3. Workspace و Owner membership اتمیک ساخته می‌شوند.
4. Activity ثبت و صفحهٔ Workspace باز می‌شود.
5. Empty State ساخت Project نمایش داده می‌شود.

پذیرش: creator دقیقاً یک `OWNER` membership دارد؛ خطای میانی هیچ رکورد نیمه‌کاره باقی نمی‌گذارد.

## UC-03 مدیریت عضو Workspace

1. Owner/Admin صفحهٔ Members را باز می‌کند.
2. Email و Role انتخاب می‌شود.
3. User موجود مستقیماً عضو می‌شود؛ User ناموجود Invitation pending می‌گیرد.
4. Duplicate membership با `409` رد می‌شود.
5. Activity و Notification مناسب ثبت می‌شود.

مجوز: Admin نمی‌تواند Owner را تغییر/حذف کند؛ Member کنترل را نمی‌بیند و API نیز `403` می‌دهد؛ Project Manager فقط در Scope محدود Project عمل می‌کند.

## UC-04 ساخت و مدیریت Project

1. Owner/Admin/Project Manager نام، Key، توضیح، رنگ و تاریخ را ثبت می‌کند.
2. در یک Transaction، Project، creator به‌عنوان manager و پنج ستون پیش‌فرض ساخته می‌شوند.
3. Activity ثبت و Overview باز می‌شود.
4. مدیر اعضای Workspace را به Project خصوصی اضافه می‌کند.

پذیرش: Key در Workspace unique است؛ عضو Workspace بدون Project membership Project خصوصی را نمی‌بیند.

## UC-05 Project Overview

نمایش: نام، توضیح، Status، بازهٔ زمانی، درصد پیشرفت، total/completed/overdue، اعضا، فعالیت اخیر و Taskهای نزدیک موعد.

عملیات مجاز: Edit، تغییر Status، رفتن به Board، افزودن Member و ساخت Task.

## UC-06 Board و Task

1. کاربر ستون‌ها و Task cardها را می‌بیند.
2. Task را در ستون می‌سازد یا جست‌وجو/فیلتر می‌کند.
3. در Drag start یک snapshot ذخیره می‌شود.
4. Drag over UI را optimistic تغییر می‌دهد.
5. Drag end درخواست Move با version می‌فرستد.
6. پاسخ موفق Cache را با دادهٔ Server sync می‌کند.
7. خطا rollback و toast فارسی؛ conflict داده را refetch می‌کند.

پذیرش: reorder داخل/بین ستون بعد از Refresh حفظ شود؛ Done و `completed_at` همگام؛ Keyboard DnD و RTL قابل استفاده؛ Member فقط در Scope مجاز.

## UC-07 جزئیات Task

Task detail در Sheet/Modal بزرگ و با URL قابل Refresh/Share مانند `?task=<id>` باز می‌شود.

کاربر متناسب با Permission می‌تواند عنوان، توضیح، Priority، تاریخ، Label، Assignee و ستون را تغییر دهد؛ Checklist، Subtask، Comment و Attachment بسازد؛ Activity را ببیند؛ لینک را Copy یا Task را Archive کند.

پذیرش: optimistic conflict مدیریت شود؛ فایل پس از size/MIME/permission بررسی شود؛ Comment editing ownership را رعایت کند؛ Checklist progress صحیح باشد.

## UC-08 نماهای مشترک Project

همهٔ نماها از API و Task source مشترک استفاده می‌کنند:

- List: جدول Task، Status، Priority، Assignee، Label، dates، completion و updated؛ Search/Sort/Filter/Pagination
- Timeline: محور روز/هفته، bar تاریخ‌دار، گروه‌بندی، zoom، overdue و بخش بدون تاریخ؛ در MVP read-only یا drag محدود
- Calendar: ماهانه و در صورت Scope هفتگی، due-date، ایجاد از روز، فیلتر و نمایش Persian locale
- Dashboard: total/open/completed، completion، overdue/due soon/unassigned، status/priority/workload و recent activity

پذیرش: Filter state قابل فهم و URL-based؛ UTC در API و Locale در نمایش؛ chart responsive و دارای summary متنی.

## UC-09 داشبورد سراسری

کاربر در `/app` active workspaces/projects، Taskهای خود، overdue، امروز، هفت روز آینده، completion 30 روزه و recent activity را می‌بیند و از shortcutها Entity جدید می‌سازد.

فرمول‌ها:

- completed: ستون `is_done=true`
- overdue: موعد گذشته و کامل‌نشده
- due soon: از اکنون تا هفت روز و کامل‌نشده
- completion rate: completed / total × 100؛ برای total صفر، مقدار صفر

## UC-10 Notification

Bell تعداد unread و آخرین اعلان‌ها را نشان می‌دهد؛ صفحهٔ کامل mark-one/mark-all و navigation به Entity دارد. Polling در Tab فعال هر 30 ثانیه، focus مجدد و پس از mutation مرتبط اجرا می‌شود.

پذیرش: Self-notification و Drag spam وجود ندارد؛ Reminder تکراری deduplicate می‌شود.

## UC-11 Profile

کاربر نام، Avatar و Timezone را تغییر می‌دهد، Locale را می‌بیند و Logout می‌کند. تغییر Password در فاز تکمیلی است.

پذیرش: persistence، validation فایل Avatar و پاک‌شدن کامل auth state در Logout.

## UC-12 Search، Filter و Sort

Search روی title و مقدار محدود description و در صورت نیاز assignee name است. Filterها: column، assignee، label، priority، date range، overdue، completed و unassigned. Sortها فقط `created_at`, `updated_at`, `due_at`, `priority`, `title`, `position`.

پذیرش: Query allowlist، pagination، URL persistence، حالت no result و عدم SQL injection از Sort field.

## سناریوی پذیرش End-to-End

1. Register/Login
2. ساخت Workspace
3. افزودن عضو موجود
4. ساخت Project و ستون‌های پیش‌فرض
5. ساخت Task و Assign
6. Drag به Done
7. افزودن Checklist و Attachment
8. مشاهده Dashboard
9. اثبات اینکه Member به Admin action دسترسی ندارد
10. Logout/Login و persistence داده

