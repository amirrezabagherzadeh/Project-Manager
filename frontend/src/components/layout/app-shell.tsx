import type { ReactNode } from "react"

import { MobileNavigation } from "@/components/layout/mobile-navigation"
import { Navigation } from "@/components/layout/navigation"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { messages } from "@/messages/fa"

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh md:flex">
      <a
        href="#main-content"
        className="fixed start-4 top-4 -translate-y-24 rounded-md bg-primary px-4 py-2 text-primary-foreground transition-transform focus:translate-y-0"
      >
        {messages.app.skipToContent}
      </a>

      <aside className="hidden w-64 shrink-0 border-e bg-card p-5 md:flex md:flex-col md:gap-6">
        <div>
          <p className="font-semibold">{messages.app.name}</p>
          <p className="text-sm text-muted-foreground">{messages.foundation.eyebrow}</p>
        </div>
        <Navigation />
      </aside>

      <div className="min-w-0 flex-1">
        <div className="flex min-h-16 items-center justify-between border-b px-4 md:px-8">
          <MobileNavigation />
          <p className="text-sm font-medium md:hidden">{messages.app.name}</p>
          <ThemeToggle />
        </div>

        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto flex w-full max-w-6xl flex-col gap-10 p-4 py-8 md:p-8"
        >
          {children}
        </main>
      </div>
    </div>
  )
}
