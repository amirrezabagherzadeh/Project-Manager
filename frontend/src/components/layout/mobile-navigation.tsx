"use client"

import { MenuIcon } from "lucide-react"

import { Navigation } from "@/components/layout/navigation"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { messages } from "@/messages/fa"

export function MobileNavigation() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="md:hidden"
          aria-label={messages.app.openNavigation}
          title={messages.app.openNavigation}
        >
          <MenuIcon aria-hidden="true" />
        </Button>
      </SheetTrigger>
      <SheetContent closeLabel={messages.app.closeNavigation}>
        <SheetHeader>
          <SheetTitle>{messages.app.name}</SheetTitle>
          <SheetDescription>{messages.foundation.eyebrow}</SheetDescription>
        </SheetHeader>
        <Navigation />
      </SheetContent>
    </Sheet>
  )
}
