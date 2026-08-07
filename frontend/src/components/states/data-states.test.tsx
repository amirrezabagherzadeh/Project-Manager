import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import {
  EmptyState,
  ErrorState,
  LoadingState,
  PermissionState,
} from "@/components/states/data-states"
import { messages } from "@/messages/fa"

describe("baseline data states", () => {
  it("renders Persian loading, empty, error, and permission patterns", () => {
    const { rerender } = render(<LoadingState />)
    expect(screen.getByLabelText(messages.states.loadingTitle)).toHaveAttribute(
      "aria-busy",
      "true",
    )

    rerender(<EmptyState />)
    expect(screen.getByText(messages.states.emptyTitle)).toBeVisible()

    rerender(<ErrorState />)
    expect(screen.getByRole("alert")).toHaveTextContent(messages.states.errorTitle)

    rerender(<PermissionState />)
    expect(screen.getByText(messages.states.permissionTitle)).toBeVisible()
  })
})

