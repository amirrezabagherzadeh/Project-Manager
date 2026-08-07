import { afterEach, describe, expect, it, vi } from "vitest"

import { api } from "@/lib/api/client"

describe("authenticated binary downloads", () => {
  afterEach(() => vi.restoreAllMocks())

  it("sends the bearer token when downloading an attachment", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "download-token", token_type: "bearer" }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response("attachment", { status: 200 }))

    await api.login("member@example.com", "a-secure-password")
    const blob = await api.downloadAttachment("attachment-id")

    expect(await blob.text()).toBe("attachment")
    const headers = fetchMock.mock.calls[1][1]?.headers as Headers
    expect(headers.get("Authorization")).toBe("Bearer download-token")
    expect(fetchMock.mock.calls[1][1]?.credentials).toBe("include")
  })
})
