import { BookOpenIcon, HomeIcon, Layers3Icon } from "lucide-react"

import { messages } from "@/messages/fa"

const navigationItems = [
  { label: messages.navigation.home, href: "#main-content", icon: HomeIcon },
  { label: messages.navigation.foundation, href: "#states-heading", icon: Layers3Icon },
  {
    label: messages.navigation.documentation,
    href: "http://127.0.0.1:8000/docs",
    icon: BookOpenIcon,
  },
]

export function Navigation() {
  return (
    <nav aria-label={messages.app.navigationLabel}>
      <ul className="flex flex-col gap-1">
        {navigationItems.map(({ label, href, icon: Icon }) => (
          <li key={label}>
            <a
              href={href}
              className="flex min-h-10 items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <Icon aria-hidden="true" />
              <span>{label}</span>
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

