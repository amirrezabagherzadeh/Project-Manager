# راهنمای طراحی محصول

## اصول تجربه

محصول باید حرفه‌ای، مدرن، مینیمال و آرام باشد؛ برای استفادهٔ طولانی‌مدت، نه یک Demo پرزرق‌وبرق. اطلاعات، وضعیت و اقدام اصلی باید در نگاه اول روشن باشند. هر Feature در Light و Dark Mode، Desktop و Mobile، RTL و Keyboard بررسی می‌شود.

## زبان و RTL

- Root: `<html lang="fa" dir="rtl">`
- از propertyهای منطقی `start/end` به‌جای `left/right` استفاده شود.
- Sidebar دسکتاپ سمت راست؛ Mobile داخل Sheet.
- Iconهای جهت‌دار در RTL flip شوند؛ iconهای معنایی بی‌دلیل flip نشوند.
- Dialog، Popover، Dropdown، Tooltip و Portalها `dir="rtl"` دریافت کنند.
- Breadcrumb، Pagination، Table، Calendar و Drag & Drop تست RTL داشته باشند.
- تمام متن‌های کاربرمحور در `messages/fa.ts`؛ Field، Enum، URL و Code انگلیسی و پایدار.
- ارقام فارسی/عربی هنگام ورود normalize و به Backend به‌شکل استاندارد ارسال شوند.
- تاریخ API همیشه ISO؛ نمایش می‌تواند با `fa-IR-u-ca-persian` باشد.

## تایپوگرافی

ترتیب ترجیح فونت: Vazirmatn با مجوز و بارگذاری بهینه، سپس `Noto Sans Arabic`, `Tahoma`, `sans-serif`.

- Page title: 24–30px
- Section title: 18–20px
- Body: 14–16px
- Metadata: 12–13px
- Line height برای متن فارسی سخاوتمندانه و truncation فقط با دسترسی به متن کامل

## Layout

Desktop:

```text
[Right Sidebar] [Topbar + Page header + Main content]
```

Sidebar شامل Product، Workspace switcher، Dashboard، Projects، Members، Notifications، Settings و User menu است.

Mobile:

- Topbar و Hamburger
- Navigation داخل Sheet
- Board با horizontal scroll و targetهای لمسی مناسب
- Task detail به‌صورت full-screen Sheet/Drawer
- Action اصلی در دسترس، بدون تراکم کنترل دسکتاپ

## Design tokens

فقط Semantic tokenها استفاده شوند:

```text
background, foreground, card, muted, border,
primary, primary-foreground, destructive,
success, warning, info
```

رنگ به‌تنهایی حامل معنا نیست؛ Status همراه متن و/یا Icon است. Colorهای Label/Project باید contrast قابل قبول در هر دو Theme داشته باشند.

## Component inventory

- Shell: `AppSidebar`, `MobileSidebar`, `Topbar`, `WorkspaceSwitcher`, `UserMenu`, `NotificationBell`, `Breadcrumbs`, `PageHeader`
- Workspace: `WorkspaceCard`, `WorkspaceForm`, `MemberTable`, `MemberRoleSelect`, `InviteMemberDialog`
- Project: `ProjectCard`, `ProjectStatusBadge`, `ProjectTabs`, `ProjectForm`, `ProjectMemberAvatarGroup`, `ProjectProgress`
- Board: `BoardToolbar`, `BoardColumn`, `BoardColumnHeader`, `TaskCard`, `AddTaskComposer`, `DragOverlayTaskCard`, `BoardFilters`, `ColumnMenu`
- Task: `TaskDetailSheet`, editors، pickers، `ChecklistPanel`, `SubtaskList`, `CommentThread`, `AttachmentList`, `ActivityTimeline`
- Dashboard: `MetricCard`, charts، `OverdueTasksCard`, `UpcomingTasksCard`, `RecentActivity`

Feature componentها باید primitiveهای `components/ui` را compose کنند؛ fork بی‌دلیل shadcn primitive یا style hardcoded ممنوع است.

## حالت‌های الزامی

هر Page و Data region باید متناسب با Scope این حالت‌ها را طراحی کند:

- Loading با Skeleton مرتبط، نه Spinner تنها
- Empty با توضیح و اقدام بعدی
- Error با پیام فارسی و Retry امن
- Permission denied بدون افشای Resource
- Success و optimistic pending
- Partial data
- No search result همراه Clear filters
- Archived با محدودیت اقدام روشن
- Offline/network error

## Board

- ستون‌ها در Desktop عرض پایدار و scroll افقی؛ cardها hierarchy روشن دارند.
- Title، Priority، Assignee، Label، Due و Checklist progress فقط در صورت ارزش اطلاعاتی نشان داده شوند.
- Drag overlay سبک و واضح؛ drop target و keyboard instructions قابل درک.
- WIP limit با متن/عدد و warning نشان داده شود.
- optimistic move نباید card را گم کند؛ rollback بصری و toast لازم است.

## فرم و Feedback

- Label صریح، error متصل به input و helper text مختصر
- Submit pending جلوی تکرار را بگیرد، ولی cancel/close را بی‌دلیل قفل نکند.
- پیام‌های API با جدول code-to-message فارسی map شوند.
- Toast برای نتیجهٔ کوتاه؛ خطای نیازمند اصلاح نزدیک field یا region نمایش داده شود.
- Confirm dialog فقط برای اقدام پرخطر؛ Archive مسیر معمول Project/Task است.

## Accessibility

- ترتیب Focus مطابق RTL و ساختار بصری
- `:focus-visible` واضح
- Focus trap و بازگشت Focus در Dialog/Sheet
- Button واقعی برای Action؛ link برای Navigation
- `aria-label` برای icon-only control
- target لمسی حداقل مناسب و contrast استاندارد
- DnD با Keyboard و alternative move control
- Chart summary متنی و tooltip قابل Keyboard
- Motion محدود و احترام به `prefers-reduced-motion`

## Checklist پذیرش هر صفحه

- عنوان و Breadcrumb
- Loading/Empty/Error/Permission
- Responsive و RTL
- Dark mode
- Keyboard و Screen-reader basics
- Toast/error فارسی
- دادهٔ واقعی، بدون Mock دائمی
- تست حداقل مسیر بحرانی

