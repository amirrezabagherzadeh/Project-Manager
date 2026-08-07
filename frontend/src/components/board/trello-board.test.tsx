import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { TrelloBoard } from "@/components/board/trello-board"
import { messages } from "@/messages/fa"

const api = vi.hoisted(() => ({
  createTask: vi.fn(),
  getBoard: vi.fn(),
  moveTask: vi.fn(),
  startDemoSession: vi.fn(),
}))

vi.mock("@/lib/api/client", () => api)

const board = {
  workspace: { id: "workspace", name: "فضای نمونه" },
  project: { id: "project", name: "پروژه نمونه", description: null },
  columns: [{ id: "todo", name: "برای انجام", is_done: false }],
  tasks: [{ id: "task-1234", title: "اولین وظیفه", column_id: "todo", priority: "medium", version: 1 }],
}

function renderBoard() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <TrelloBoard />
    </QueryClientProvider>,
  )
}

describe("TrelloBoard", () => {
  beforeEach(() => {
    api.startDemoSession.mockResolvedValue(undefined)
    api.getBoard.mockResolvedValue(board)
  })

  it("starts the demo session and renders persisted board data", async () => {
    renderBoard()
    fireEvent.click(screen.getByRole("button", { name: messages.board.startDemo }))
    await waitFor(() => expect(screen.getByText(board.project.name)).toBeVisible())
    expect(screen.getByText(board.tasks[0].title)).toBeVisible()
    expect(screen.getByRole("textbox", { name: messages.board.newTaskLabel })).toBeVisible()
  })
})
