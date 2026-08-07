import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

import RootLayout from "@/app/layout"

vi.mock("@fontsource-variable/vazirmatn", () => ({}))

describe("RootLayout", () => {
  it("declares Persian language and right-to-left direction", () => {
    const markup = renderToStaticMarkup(
      <RootLayout>
        <main>محتوا</main>
      </RootLayout>,
    )

    expect(markup).toContain('<html lang="fa" dir="rtl"')
  })
})
