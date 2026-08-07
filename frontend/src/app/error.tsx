"use client"

import { ErrorState } from "@/components/states/data-states"

export default function GlobalError({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto w-full max-w-3xl p-6">
      <ErrorState onRetry={reset} />
    </main>
  )
}

