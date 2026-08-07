import type { Metadata } from "next"
import type { ReactNode } from "react"

import { AppProviders } from "@/components/providers/app-providers"

import "@fontsource-variable/vazirmatn"
import "./globals.css"

export const metadata: Metadata = {
  title: "مدیریت پروژه",
  description: "سامانهٔ مدیریت پروژه برای تیم‌های فارسی‌زبان",
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  )
}
