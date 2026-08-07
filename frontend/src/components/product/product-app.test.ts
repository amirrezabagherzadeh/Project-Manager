import { describe, expect, it } from "vitest"

import { timelineGeometry } from "@/components/product/product-app"

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
