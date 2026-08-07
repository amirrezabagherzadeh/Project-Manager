"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { AlertCircle, ArrowLeftRight, CheckCircle2, LoaderCircle, Plus, RefreshCw, Sparkles } from "lucide-react"
import { useState } from "react"
import { createTask, getBoard, moveTask, startDemoSession, type Task } from "@/lib/api/client"
import { messages } from "@/messages/fa"

const boardKey = ["demo-board"] as const
const priorityClass = (priority: Task["priority"]) => ({ low: "bg-sky-100 text-sky-800", medium: "bg-amber-100 text-amber-800", high: "bg-orange-100 text-orange-800", urgent: "bg-rose-100 text-rose-800" })[priority]

export function TrelloBoard() {
  const client = useQueryClient(); const [ready, setReady] = useState(false)
  const board = useQuery({ queryKey: boardKey, queryFn: getBoard, enabled: ready, staleTime: 15_000 })
  const login = useMutation({ mutationFn: startDemoSession, onSuccess: () => setReady(true) })
  const create = useMutation({ mutationFn: ({ columnId, title }: { columnId: string; title: string }) => createTask(board.data!.project.id, columnId, title), onSuccess: () => client.invalidateQueries({ queryKey: boardKey }) })
  const move = useMutation({ mutationFn: ({ task, columnId, index }: { task: Task; columnId: string; index: number }) => moveTask(task, columnId, index), onMutate: async ({ task, columnId }) => { await client.cancelQueries({ queryKey: boardKey }); const snapshot = client.getQueryData<typeof board.data>(boardKey); client.setQueryData<typeof board.data>(boardKey, value => value ? { ...value, tasks: value.tasks.map(item => item.id === task.id ? { ...item, column_id: columnId } : item) } : value); return { snapshot } }, onError: (error, _variables, context) => { client.setQueryData(boardKey, context?.snapshot); if ((error as { status?: number }).status === 409) client.invalidateQueries({ queryKey: boardKey }) }, onSuccess: () => client.invalidateQueries({ queryKey: boardKey }) })
  if (!ready) return <section className="board-welcome"><div><p className="board-kicker">{messages.board.kicker}</p><h1>{messages.board.title}</h1><p>{messages.board.description}</p></div><button className="board-primary" onClick={() => login.mutate()} disabled={login.isPending}><Sparkles size={18}/>{login.isPending ? messages.board.connecting : messages.board.startDemo}</button>{login.isError ? <p className="board-error">{messages.board.connectionError}</p> : null}</section>
  if (board.isPending) return <div className="board-loading"><LoaderCircle className="animate-spin"/><span>{messages.board.loading}</span></div>
  if (board.isError || !board.data) return <section className="board-error-state"><AlertCircle/><h1>{messages.board.errorTitle}</h1><button className="board-secondary" onClick={() => board.refetch()}><RefreshCw size={16}/>{messages.board.retry}</button></section>
  const { project, workspace, columns, tasks } = board.data
  return <section className="board-page"><header className="board-header"><div><p className="board-kicker">{workspace.name}</p><h1>{project.name}</h1><p>{project.description ?? messages.board.defaultDescription}</p></div><div className="board-stat"><CheckCircle2 size={18}/><span>{tasks.length} {messages.board.taskCount}</span></div></header><div className="board-columns" aria-label={messages.board.columnsLabel}>{columns.map(column => <BoardColumn key={column.id} column={column} tasks={tasks.filter(task => task.column_id === column.id)} columns={columns} onCreate={title => create.mutate({ columnId: column.id, title })} onMove={(task, columnId) => move.mutate({ task, columnId, index: tasks.filter(item => item.column_id === columnId).length })} pending={create.isPending || move.isPending}/>)}</div>{move.isError ? <p className="board-error floating-error">{messages.board.moveError}</p> : null}</section>
}

function BoardColumn({ column, tasks, columns, onCreate, onMove, pending }: { column: { id: string; name: string; is_done: boolean }; tasks: Task[]; columns: { id: string; name: string }[]; onCreate: (title: string) => void; onMove: (task: Task, columnId: string) => void; pending: boolean }) {
  const [title, setTitle] = useState("")
  return <article className="board-column"><header><div><span className={column.is_done ? "dot done" : "dot"}/><h2>{column.name}</h2></div><span className="column-count">{tasks.length}</span></header><div className="task-stack">{tasks.map(task => <article className="task-card" key={task.id}><div className="task-card-top"><span className={`priority ${priorityClass(task.priority)}`}>{messages.board.priorities[task.priority]}</span><span className="task-code">#{task.id.slice(0, 4)}</span></div><h3>{task.title}</h3><div className="task-actions"><ArrowLeftRight size={15}/><label className="sr-only" htmlFor={`move-${task.id}`}>{messages.board.moveLabel}</label><select id={`move-${task.id}`} value={task.column_id} disabled={pending} onChange={event => onMove(task, event.target.value)}>{columns.map(target => <option key={target.id} value={target.id}>{target.name}</option>)}</select></div></article>)}</div><form className="task-composer" onSubmit={event => { event.preventDefault(); const value = title.trim(); if (value) { onCreate(value); setTitle("") } }}><input value={title} onChange={event => setTitle(event.target.value)} placeholder={messages.board.newTaskPlaceholder} aria-label={messages.board.newTaskLabel}/><button type="submit" disabled={pending || !title.trim()} aria-label={messages.board.addTask}><Plus size={18}/></button></form></article>
}
