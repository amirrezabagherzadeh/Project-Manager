import { expect, test } from "@playwright/test"

const backend = "http://127.0.0.1:8000/api/v1"

test("authenticates, restores the session, and completes a board flow", async ({ page }, testInfo) => {
  await page.goto("/")

  await expect(page.locator("html")).toHaveAttribute("lang", "fa")
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl")
  await page.getByRole("button", { name: "ورود با حساب نمونه" }).click()
  await expect(page.locator(".product-shell")).toBeVisible()

  await page.reload()
  await expect(page.locator(".product-shell")).toBeVisible()

  if (testInfo.project.name === "mobile-chromium") {
    const menu = page.getByRole("button", { name: "بازکردن منوی ناوبری" })
    await expect(menu).toBeVisible()
    await menu.click()
    await expect(page.locator(".workspace-rail")).toHaveClass(/open/)
  }

  await page.locator(".rail-projects > button").first().click()
  await expect(page.locator(".board-surface")).toBeVisible()
  const columnName = `ستون ${testInfo.project.name}-${Date.now()}`
  await page.locator(".new-column-card input").fill(columnName)
  await page.getByRole("button", { name: "افزودن ستون" }).click()
  const addedColumn = page.locator(".trello-list").filter({ has: page.getByRole("heading", { name: columnName, exact: true }) })
  await expect(addedColumn).toBeVisible()
  await addedColumn.getByRole("button", { name: "عملیات ستون" }).click()
  page.once("dialog", (dialog) => dialog.accept(`${columnName} ویرایش‌شده`))
  await addedColumn.getByRole("menuitem", { name: "تغییر نام ستون" }).click()
  await expect(page.getByRole("heading", { name: `${columnName} ویرایش‌شده`, exact: true })).toBeVisible()
  const title = `کار مرورگر ${testInfo.project.name}-${Date.now()}`
  const composer = page.locator(".card-composer").first()
  await composer.locator("input").fill(title)
  await composer.locator("button").click()
  await expect(page.getByText(title, { exact: true })).toBeVisible()
  await page.getByText(title, { exact: true }).click()
  await expect(page.locator(".task-dialog")).toBeVisible()
  await expect(page.locator(".task-title-input")).toHaveValue(title)

  const description = `جزئیات ${title}`
  await page.locator('.task-main textarea[name="description"]').fill(description)
  await page.locator(".task-main form").first().getByRole("button", { name: "ذخیره" }).click()
  await expect(page.locator('.task-main textarea[name="description"]')).toHaveValue(description)

  const comment = `نظر ${Date.now()}`
  await page.locator(".comment-composer input").fill(comment)
  await page.getByRole("button", { name: "ارسال نظر" }).click()
  await expect(page.getByText(comment, { exact: true })).toBeVisible()
  const editedComment = `${comment} ویرایش‌شده`
  page.once("dialog", (dialog) => dialog.accept(editedComment))
  await page.locator(".comment-actions").getByRole("button", { name: "ویرایش" }).click()
  await expect(page.getByText(editedComment, { exact: true })).toBeVisible()

  page.once("dialog", (dialog) => dialog.accept("آماده‌سازی"))
  await page.getByRole("button", { name: /چک‌لیست تازه/ }).click()
  const checklist = page.locator(".checklist").last()
  await expect(checklist).toBeVisible()
  await checklist.locator('.mini-composer input[name="item"]').fill("مورد اول")
  await checklist.locator(".mini-composer button").click()
  await expect(checklist.getByText("مورد اول", { exact: true })).toBeVisible()
  await checklist.locator('.mini-composer input[name="item"]').fill("مورد دوم")
  await checklist.locator(".mini-composer button").click()
  await expect(checklist.getByText("مورد دوم", { exact: true })).toBeVisible()
  await checklist.locator(".checklist-title").fill("آماده‌سازی نهایی")
  await checklist.locator(".checklist-title").blur()
  await expect(checklist.locator(".checklist-title")).toHaveValue("آماده‌سازی نهایی")

  const attachmentName = `e2e-${Date.now()}.txt`
  await page.locator('.task-section input[type="file"]').setInputFiles({ name: attachmentName, mimeType: "text/plain", buffer: Buffer.from("validated attachment") })
  await expect(page.getByText(attachmentName, { exact: true })).toBeVisible()
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator(".attachment-download").filter({ hasText: attachmentName }).click(),
  ])
  expect(download.suggestedFilename()).toBe(attachmentName)

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
  expect(hasHorizontalOverflow).toBe(false)
})

test("enforces member permissions and reaches reporting, members, notifications, and profile", async ({ page, request }, testInfo) => {
  const stamp = `${testInfo.project.name}-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const ownerEmail = `e2e-owner-${testInfo.project.name}@example.com`
  const memberEmail = `e2e-member-${testInfo.project.name}@example.com`
  const password = "a-secure-password"
  const ensureUser = async (name: string, email: string) => {
    let tokenResponse = await request.post(`${backend}/auth/token`, { form: { username: email, password } })
    if (tokenResponse.status() === 401) {
      const registration = await request.post(`${backend}/auth/register`, { data: { name, email, password } })
      expect([201, 409]).toContain(registration.status())
      tokenResponse = await request.post(`${backend}/auth/token`, { form: { username: email, password } })
    }
    expect(tokenResponse.status()).toBe(200)
    return (await tokenResponse.json()).access_token as string
  }
  const token = await ensureUser("مالک آزمون", ownerEmail)
  await ensureUser("عضو آزمون", memberEmail)
  const headers = { Authorization: `Bearer ${token}` }
  const previous = await request.get(`${backend}/workspaces?page=1&page_size=100`, { headers })
  for (const workspace of (await previous.json()).data as Array<{ id: string }>) {
    await request.post(`${backend}/workspaces/${workspace.id}/archive`, { headers })
  }
  const workspaceResponse = await request.post(`${backend}/workspaces`, { headers, data: { name: `فضای ${stamp}` } })
  const workspaceId = (await workspaceResponse.json()).data.id as string
  expect((await request.post(`${backend}/workspaces/${workspaceId}/members`, { headers, data: { email: memberEmail, role: "MEMBER" } })).status()).toBe(201)
  expect((await request.post(`${backend}/workspaces/${workspaceId}/projects`, { headers, data: { name: `پروژه ${stamp}`, key: `E${Date.now().toString().slice(-5)}`, is_private: false } })).status()).toBe(201)

  await page.goto("/login")
  await page.locator('input[name="email"]').fill(memberEmail)
  await page.locator('input[name="password"]').fill(password)
  await page.getByRole("button", { name: "ورود به فضای کار" }).click()
  await expect(page.locator(".product-shell")).toBeVisible()
  await page.locator(".project-tile").first().click()
  await expect(page.locator(".board-surface")).toBeVisible()

  await page.getByRole("button", { name: "اعضا", exact: true }).click()
  await expect(page.locator(".member-list")).toContainText("عضو آزمون")
  await expect(page.locator(".member-list")).toContainText(memberEmail)

  await page.getByRole("button", { name: "تنظیمات", exact: true }).click()
  await expect(page.locator('.settings-grid input[name="name"]').first()).toBeDisabled()
  await expect(page.getByRole("button", { name: "حذف دائمی فضای کاری" })).toHaveCount(0)

  await page.getByRole("button", { name: "گزارش", exact: true }).click()
  await expect(page.locator(".dashboard-view")).toBeVisible()

  await page.goto("/app/notifications?view=notifications")
  await expect(page.locator(".notifications-view")).toBeVisible()
  await page.goto("/app/profile?view=profile")
  await expect(page.locator(".profile-view")).toBeVisible()
  await expect(page.locator('.profile-view input[name="email"]')).toHaveValue(memberEmail)
})
