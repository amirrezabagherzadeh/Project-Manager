import { AlertCircleIcon, LockKeyholeIcon } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { messages } from "@/messages/fa"

export function LoadingState() {
  return (
    <section
      aria-label={messages.states.loadingTitle}
      aria-busy="true"
      className="flex min-h-48 flex-col gap-4 rounded-lg border bg-card p-6"
    >
      <div className="flex flex-col gap-2">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
      <span className="sr-only">{messages.states.loadingDescription}</span>
    </section>
  )
}

export function EmptyState() {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyTitle>{messages.states.emptyTitle}</EmptyTitle>
        <EmptyDescription>{messages.states.emptyDescription}</EmptyDescription>
      </EmptyHeader>
    </Empty>
  )
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <Alert variant="destructive" className="min-h-48 content-center">
      <AlertCircleIcon aria-hidden="true" />
      <AlertTitle>{messages.states.errorTitle}</AlertTitle>
      <AlertDescription className="flex flex-col items-start gap-4">
        <span>{messages.states.errorDescription}</span>
        {onRetry ? (
          <Button type="button" variant="outline" onClick={onRetry}>
            {messages.states.retry}
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  )
}

export function PermissionState() {
  return (
    <Empty>
      <LockKeyholeIcon aria-hidden="true" />
      <EmptyHeader>
        <EmptyTitle>{messages.states.permissionTitle}</EmptyTitle>
        <EmptyDescription>{messages.states.permissionDescription}</EmptyDescription>
      </EmptyHeader>
      <EmptyContent />
    </Empty>
  )
}

