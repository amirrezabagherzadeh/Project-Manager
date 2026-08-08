import { afterEach, describe, expect, it, vi } from "vitest"

import { registerAndAuthenticate, timelineGeometry } from "@/components/product/product-app"
import { api, type User } from "@/lib/api/client"

afterEach(() => vi.restoreAllMocks())

describe("registration", () => {
  it("logs the new user in and loads their identity", async () => {
    const user = {
      id: "8b02464d-932d-4f30-8e8d-9b6b1ef4762b",
      email: "new@example.com",
      name: "New User",
      is_active: true,
      timezone: "Asia/Tehran",
      avatar_content_type: null,
      created_at: "2026-08-09T00:00:00Z",
      updated_at: "2026-08-09T00:00:00Z",
    } satisfies User
    const register = vi.spyOn(api, "register").mockResolvedValue({ data: user })
    const login = vi.spyOn(api, "login").mockResolvedValue({
      access_token: "new-user-token",
      token_type: "bearer",
    })
    const me = vi.spyOn(api, "me").mockResolvedValue({ data: user })

    await expect(
      registerAndAuthenticate("New User", "new@example.com", "a-secure-password"),
    ).resolves.toEqual(user)

    expect(register).toHaveBeenCalledWith({
      name: "New User",
      email: "new@example.com",
      password: "a-secure-password",
    })
    expect(login).toHaveBeenCalledWith("new@example.com", "a-secure-password")
    expect(me).toHaveBeenCalledOnce()
    expect(register.mock.invocationCallOrder[0]).toBeLessThan(login.mock.invocationCallOrder[0])
    expect(login.mock.invocationCallOrder[0]).toBeLessThan(me.mock.invocationCallOrder[0])
  })
})

describe("timelineGeometry", () => {
  it("positions a task from its persisted creation and due dates", () => {
    const geometry = timelineGeometry(
      { created_at: "2026-01-03T00:00:00.000Z", due_at: "2026-01-07T00:00:00.000Z" },
      "2026-01-01T00:00:00.000Z",
      "2026-01-11T00:00:00.000Z",
    )
    expect(geometry.left).toBe(20)
    expect(geometry.width).toBe(40)
  })

  it("clamps dates to the visible range", () => {
    const geometry = timelineGeometry(
      { created_at: "2025-12-01T00:00:00.000Z", due_at: "2027-01-01T00:00:00.000Z" },
      "2026-01-01T00:00:00.000Z",
      "2026-01-11T00:00:00.000Z",
    )
    expect(geometry).toEqual({ left: 0, width: 100 })
  })
})
