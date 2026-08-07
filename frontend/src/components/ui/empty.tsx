import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

function Empty({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="empty"
      className={cn(
        "flex min-h-48 w-full flex-col items-center justify-center gap-6 rounded-lg border border-dashed p-6 text-center",
        className,
      )}
      {...props}
    />
  )
}

function EmptyHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="empty-header"
      className={cn("flex max-w-sm flex-col items-center gap-2", className)}
      {...props}
    />
  )
}

function EmptyTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 data-slot="empty-title" className={cn("font-medium", className)} {...props} />
  )
}

function EmptyDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      data-slot="empty-description"
      className={cn("text-sm leading-6 text-muted-foreground", className)}
      {...props}
    />
  )
}

function EmptyContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div data-slot="empty-content" className={cn("flex gap-2", className)} {...props} />
}

export { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyTitle }

