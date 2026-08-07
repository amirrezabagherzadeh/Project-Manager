import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"

import { MobileNavigation } from "@/components/layout/mobile-navigation"
import { messages } from "@/messages/fa"

describe("MobileNavigation", () => {
  it("opens an accessible RTL navigation sheet", async () => {
    const user = userEvent.setup()
    render(<MobileNavigation />)

    await user.click(screen.getByRole("button", { name: messages.app.openNavigation }))

    expect(screen.getByRole("dialog")).toHaveAttribute("dir", "rtl")
    expect(screen.getByRole("heading", { name: messages.app.name })).toBeVisible()
    expect(screen.getByRole("navigation", { name: messages.app.navigationLabel })).toBeVisible()
  })
})

