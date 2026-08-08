"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import Image from "next/image"
import {
  Archive, ArrowDown, ArrowUp, Bell, CalendarDays, ChartNoAxesCombined, Check, CheckCircle2, ChevronDown,
  Circle, Clock3, Columns3, LayoutDashboard, List, LoaderCircle, LogOut, Menu,
  MessageSquare, MoreHorizontal, Paperclip, Pencil, Plus, RotateCcw, Search, Settings,
  Users, X,
} from "lucide-react"
import { type DragEvent, type ReactNode, useCallback, useEffect, useMemo, useState } from "react"
import {
  api, ApiError, refreshAccessToken, type Activity, type Column, type Notification, type Project,
  type Task, type User, type Workspace,
} from "@/lib/api/client"
import { messages } from "@/messages/fa"

const m = messages.product
type View = "home" | "board" | "list" | "timeline" | "calendar" | "dashboard" | "members" | "settings" | "notifications" | "profile"
const viewItems: { id: View; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "board", label: m.nav.board, icon: Columns3 },
  { id: "list", label: m.nav.list, icon: List },
  { id: "timeline", label: m.nav.timeline, icon: Clock3 },
  { id: "calendar", label: m.nav.calendar, icon: CalendarDays },
  { id: "dashboard", label: m.nav.dashboard, icon: ChartNoAxesCombined },
  { id: "members", label: m.nav.members, icon: Users },
  { id: "settings", label: m.nav.settings, icon: Settings },
]
const priorities = ["low", "medium", "high", "urgent"] as const
const initialView = (): View => {
  if (typeof window === "undefined") return "home"
  const requested = new URLSearchParams(window.location.search).get("view") as View | null
  return requested && ["home", ...viewItems.map((item) => item.id), "notifications", "profile"].includes(requested) ? requested : "home"
}
const initialTask = () => {
  if (typeof window === "undefined") return null
  const queryTask = new URLSearchParams(window.location.search).get("task")
  const pathTask = window.location.pathname.match(/^\/app\/tasks\/([^/]+)/)?.[1]
  return queryTask ?? pathTask ?? null
}
const dateText = (value?: string | null) => value ? new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" }).format(new Date(value)) : m.task.noDueDate
const initials = (value: string) => value.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()
const errorText = (error: unknown) => {
  const code = error instanceof ApiError ? error.code : "request_failed"
  return m.errors[code as keyof typeof m.errors] ?? m.errors.request_failed
}

export function timelineGeometry(task: Pick<Task, "created_at" | "due_at">, rangeStart: string, rangeEnd: string) {
  const min = new Date(rangeStart).getTime()
  const max = new Date(rangeEnd).getTime()
  const span = Math.max(1, max - min)
  const taskStart = Math.min(max, Math.max(min, new Date(task.created_at).getTime()))
  const fallbackEnd = taskStart + 24 * 60 * 60 * 1000
  const taskEnd = Math.min(max, Math.max(taskStart, task.due_at ? new Date(task.due_at).getTime() : fallbackEnd))
  return { left: (taskStart - min) / span * 100, width: Math.max(1.5, (taskEnd - taskStart) / span * 100) }
}

export async function registerAndAuthenticate(name: string, email: string, password: string) {
  await api.register({ name, email, password })
  await api.login(email, password)
  return (await api.me()).data
}

async function saveAttachment(id: string, name: string) {
  const blob = await api.downloadAttachment(id)
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(url)
}

export function ProductApp({ initialMode = "login", inviteToken }: { initialMode?: "login" | "register"; inviteToken?: string } = {}) {
  const client = useQueryClient()
  const [session, setSession] = useState<"booting" | "anonymous" | "authenticated">("booting")
  const [me, setMe] = useState<User | null>(null)
  const [workspaceId, setWorkspaceId] = useState("")
  const [projectId, setProjectId] = useState("")
  const [view, setView] = useState<View>(initialView)
  const [taskId, setTaskId] = useState<string | null>(initialTask)
  const [railOpen, setRailOpen] = useState(false)
  const [inviteStatus, setInviteStatus] = useState<"idle" | "accepting" | "accepted" | "error">("idle")
  const processInvite = useCallback(async () => {
    if (!inviteToken) return
    setInviteStatus("accepting")
    try {
      await api.acceptInvitation(inviteToken)
      await client.invalidateQueries({ queryKey: ["workspaces"] })
      setInviteStatus("accepted")
    } catch { setInviteStatus("error") }
  }, [client, inviteToken])

  useEffect(() => {
    let active = true
    const bootstrap = async () => {
      if (!await refreshAccessToken()) { if (active) setSession("anonymous"); return }
      try {
        const identity = (await api.me()).data
        if (active) { setMe(identity); setSession("authenticated"); void processInvite() }
      } catch { if (active) setSession("anonymous") }
    }
    void bootstrap()
    return () => { active = false }
  }, [processInvite])

  const navigate = (next: View, selectedTask: string | null = null) => {
    setView(next); setTaskId(selectedTask); setRailOpen(false)
    const query = new URLSearchParams()
    query.set("view", next)
    if (selectedTask) query.set("task", selectedTask)
    window.history.pushState({}, "", `/app/${next}?${query.toString()}`)
  }

  if (session === "booting") return <FullLoader />
  if (session === "anonymous" || !me) return <AuthScreen initialMode={initialMode} onAuthenticated={(user) => { setMe(user); setSession("authenticated"); void processInvite() }} />

  return <>{inviteStatus !== "idle" ? <div className={`invite-status ${inviteStatus}`}>{inviteStatus === "accepting" ? m.member.accepting : inviteStatus === "accepted" ? m.member.accepted : m.errors.request_failed}</div> : null}<AppWorkspace
    me={me} workspaceId={workspaceId} projectId={projectId} view={view} taskId={taskId}
    railOpen={railOpen} onRailOpen={setRailOpen} onWorkspace={setWorkspaceId}
    onProject={setProjectId} onNavigate={navigate} onMe={setMe}
    onLogout={async () => { await api.logout(); client.clear(); setMe(null); setSession("anonymous") }}
  /></>
}

function AuthScreen({ onAuthenticated, initialMode }: { onAuthenticated: (user: User) => void; initialMode: "login" | "register" }) {
  const [mode, setMode] = useState<"login" | "register">(initialMode)
  const auth = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const data = new FormData(form)
      const email = String(data.get("email") ?? "").trim()
      const password = String(data.get("password") ?? "")
      if (!email.includes("@") || password.length < 8) throw new ApiError(m.auth.invalid, 422)
      if (mode === "register") {
        return registerAndAuthenticate(String(data.get("name") ?? "").trim(), email, password)
      }
      await api.login(email, password)
      return (await api.me()).data
    },
    onSuccess: onAuthenticated,
  })
  const demo = useMutation({ mutationFn: async () => { await api.login("demo@example.com", "demo-password-change-me"); return (await api.me()).data }, onSuccess: onAuthenticated })
  return <main className="auth-page">
    <section className="auth-story" aria-hidden="true">
      <div className="brand-mark"><Columns3 /><span>{m.brand}</span></div>
      <div><p className="eyebrow">{m.tagline}</p><h1>{m.auth.welcome}</h1><p>{m.auth.description}</p></div>
      <div className="auth-board-preview"><span/><span/><span/></div>
    </section>
    <section className="auth-panel">
      <div className="auth-card">
        <div className="auth-mobile-brand"><Columns3 /> {m.brand}</div>
        <div className="segmented"><button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>{m.auth.login}</button><button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>{m.auth.register}</button></div>
        <form onSubmit={(event) => { event.preventDefault(); auth.mutate(event.currentTarget) }}>
          {mode === "register" ? <Field name="name" label={m.auth.name} autoComplete="name" /> : null}
          <Field name="email" label={m.auth.email} type="email" autoComplete="email" dir="ltr" />
          <Field name="password" label={m.auth.password} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} dir="ltr" />
          {auth.isError ? <ErrorNote error={auth.error} /> : null}
          <button className="primary wide" disabled={auth.isPending}>{auth.isPending ? <LoaderCircle className="spin"/> : null}{mode === "login" ? m.auth.submitLogin : m.auth.submitRegister}</button>
        </form>
        <button className="ghost wide" disabled={demo.isPending} onClick={() => demo.mutate()}>{m.auth.demo}</button>
        {demo.isError ? <ErrorNote error={demo.error} /> : null}
      </div>
    </section>
  </main>
}

function AppWorkspace(props: {
  me: User; workspaceId: string; projectId: string; view: View; taskId: string | null; railOpen: boolean
  onRailOpen: (value: boolean) => void; onWorkspace: (id: string) => void; onProject: (id: string) => void
  onNavigate: (view: View, task?: string | null) => void; onMe: (user: User) => void; onLogout: () => Promise<void>
}) {
  const { me, view, taskId } = props
  const [search, setSearch] = useState("")
  const [composer, setComposer] = useState<"workspace" | "project" | null>(null)
  const [appError, setAppError] = useState("")
  const client = useQueryClient()
  const workspaces = useQuery({ queryKey: ["workspaces", "all"], queryFn: () => api.workspaces(true), staleTime: 120_000 })
  const workspaceId = props.workspaceId || workspaces.data?.data.find((item) => !item.archived_at)?.id || workspaces.data?.data[0]?.id || ""
  const projects = useQuery({ queryKey: ["projects", workspaceId, "all"], queryFn: () => api.projects(workspaceId, true), enabled: Boolean(workspaceId) })
  const projectId = props.projectId || projects.data?.data.find((item) => !item.archived_at)?.id || projects.data?.data[0]?.id || ""
  const workspace = workspaces.data?.data.find((item) => item.id === workspaceId)
  const project = projects.data?.data.find((item) => item.id === projectId)
  const workspaceMembers = useQuery({ queryKey: ["workspace-members", workspaceId], queryFn: () => api.workspaceMembers(workspaceId), enabled: Boolean(workspaceId) })
  const myWorkspaceRole = workspaceMembers.data?.data.find((member) => member.user_id === me.id)?.role
  const canManageWorkspace = workspace?.owner_id === me.id || myWorkspaceRole === "OWNER" || myWorkspaceRole === "ADMIN"
  const projectMembers = useQuery({ queryKey: ["project-members", projectId], queryFn: () => api.projectMembers(projectId), enabled: Boolean(projectId) })
  const myProjectRole = projectMembers.data?.data.find((member) => member.user_id === me.id)?.role
  const canManageProject = canManageWorkspace || myProjectRole === "manager"
  const unread = useQuery({ queryKey: ["notification-count"], queryFn: api.unreadCount, refetchInterval: () => typeof document !== "undefined" && document.visibilityState === "visible" ? 30_000 : false })

  useEffect(() => { if (!props.workspaceId && workspaceId) props.onWorkspace(workspaceId) }, [props, workspaceId])
  useEffect(() => { if (!props.projectId && projectId) props.onProject(projectId) }, [props, projectId])
  useEffect(() => {
    const rejected = (event: PromiseRejectionEvent) => { if (event.reason instanceof ApiError) { event.preventDefault(); setAppError(errorText(event.reason)) } }
    window.addEventListener("unhandledrejection", rejected)
    return () => window.removeEventListener("unhandledrejection", rejected)
  }, [])
  useEffect(() => {
    if (!taskId || props.projectId) return
    void api.task(taskId).then((task) => api.project(task.data.project_id)).then((result) => { props.onWorkspace(result.data.workspace_id); props.onProject(result.data.id) }).catch((error) => setAppError(errorText(error)))
  }, [props, taskId])

  const createWorkspace = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.createWorkspace({ name: String(data.get("name")), description: String(data.get("description")) || null }) }, onSuccess: (result) => { client.invalidateQueries({ queryKey: ["workspaces"] }); props.onWorkspace(result.data.id); setComposer(null) } })
  const createProject = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.createProject(workspaceId, { name: String(data.get("name")), key: String(data.get("key")).toUpperCase(), is_private: false }) }, onSuccess: (result) => { client.invalidateQueries({ queryKey: ["projects", workspaceId] }); props.onProject(result.data.id); props.onNavigate("board"); setComposer(null) } })

  return <main className="product-shell">
    <a className="skip-link" href="#main-content">{messages.app.skipToContent}</a>
    <header className="topbar">
      <button className="icon-button mobile-only" aria-label={messages.app.openNavigation} onClick={() => props.onRailOpen(true)}><Menu/></button>
      <button className="brand" onClick={() => props.onNavigate("home")}><span className="brand-icon"><Columns3/></span><span>{m.brand}</span></button>
      <label className="global-search"><Search/><span className="sr-only">{m.search}</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={m.search}/></label>
      <button className="create-button" onClick={() => setComposer(workspaceId ? "project" : "workspace")}><Plus/>{m.create}</button>
      <div className="top-actions">
        <button className="icon-button notification-button" aria-label={m.nav.notifications} onClick={() => props.onNavigate("notifications")}><Bell/>{(unread.data?.data ?? 0) > 0 ? <span>{unread.data?.data}</span> : null}</button>
        <button className="avatar" aria-label={m.nav.profile} onClick={() => props.onNavigate("profile")}>{initials(me.name)}</button>
      </div>
    </header>
    <aside className={`workspace-rail ${props.railOpen ? "open" : ""}`}>
      <div className="rail-head"><p>{m.workspace.title}</p><button className="icon-button mobile-only" onClick={() => props.onRailOpen(false)}><X/></button></div>
      <button className={`rail-link ${view === "home" ? "active" : ""}`} onClick={() => props.onNavigate("home")}><LayoutDashboard/>{m.nav.home}</button>
      <div className="workspace-list">
        {workspaces.data?.data.map((item) => <button key={item.id} className={`${item.id === workspaceId ? "active" : ""} ${item.archived_at ? "archived" : ""}`} onClick={() => { props.onWorkspace(item.id); props.onProject(""); props.onNavigate("home") }}><span className="workspace-avatar">{initials(item.name)}</span><span>{item.name}</span>{item.archived_at ? <Archive/> : <ChevronDown/>}</button>)}
      </div>
      {canManageWorkspace || !workspaceId ? <button className="rail-add" onClick={() => setComposer("workspace")}><Plus/>{m.workspace.create}</button> : null}
      <div className="rail-projects"><div className="rail-section-title"><span>{m.workspace.projects}</span>{canManageWorkspace ? <button onClick={() => setComposer("project")}><Plus/></button> : null}</div>{projects.data?.data.map((item) => <button key={item.id} className={`${item.id === projectId ? "active" : ""} ${item.archived_at ? "archived" : ""}`} onClick={() => { props.onProject(item.id); props.onNavigate(item.archived_at ? "settings" : "board") }}><span style={{ background: item.color ?? "#0c66e4" }}/><b>{item.name}</b><small>{item.archived_at ? m.workspace.archived : item.key}</small></button>)}</div>
      <div className="rail-account"><button onClick={() => props.onNavigate("profile")}><span className="avatar small">{initials(me.name)}</span><span><b>{me.name}</b><small>{me.email}</small></span></button><button className="icon-button" aria-label={m.auth.logout} onClick={() => void props.onLogout()}><LogOut/></button></div>
    </aside>
    <section className="product-canvas">
      {project && !["home", "notifications", "profile"].includes(view) ? <ProjectHeader project={project} view={view} navigate={props.onNavigate} /> : null}
      <div id="main-content" className="view-content">
        {workspaces.isPending ? <InlineLoader/> : workspaces.isError ? <ErrorState error={workspaces.error} retry={() => workspaces.refetch()}/> : null}
        {!workspaces.isPending && !workspaces.data?.data.length ? <EmptyState text={m.workspace.empty} action={canManageWorkspace ? m.workspace.create : undefined} onAction={() => setComposer("workspace")}/> : null}
        {view === "home" && workspace ? <GlobalHome workspace={workspace} projects={projects.data?.data ?? []} onProject={(id) => { props.onProject(id); props.onNavigate("board") }} canManage={canManageWorkspace} onCreate={() => setComposer("project")}/> : null}
        {view === "notifications" ? <Notifications onOpen={async (item) => { if (!item.entity_id) return; if (item.entity_type === "task") { const task = await api.task(item.entity_id); const targetProject = await api.project(task.data.project_id); props.onWorkspace(targetProject.data.workspace_id); props.onProject(targetProject.data.id); props.onNavigate("board", task.data.id) } else if (item.entity_type === "project") { const targetProject = await api.project(item.entity_id); props.onWorkspace(targetProject.data.workspace_id); props.onProject(targetProject.data.id); props.onNavigate("board") } else { props.onWorkspace(item.entity_id); props.onProject(""); props.onNavigate("home") } }}/> : null}
        {view === "profile" ? <Profile user={me} onUser={props.onMe}/> : null}
        {project && view === "board" ? <Board project={project} search={search} canWrite={canManageProject || myProjectRole === "member"} onTask={(id) => props.onNavigate("board", id)}/> : null}
        {project && view === "list" ? <TaskList project={project} search={search} onTask={(id) => props.onNavigate("list", id)}/> : null}
        {project && (view === "timeline" || view === "calendar") ? <DateView project={project} mode={view}/> : null}
        {project && view === "dashboard" ? <ProjectDashboard project={project}/> : null}
        {workspace && view === "members" ? <Members workspace={workspace} project={project} canManageWorkspace={canManageWorkspace} canManageProject={canManageProject}/> : null}
        {workspace && view === "settings" ? <SettingsView workspace={workspace} project={project} canManageWorkspace={canManageWorkspace} canManageProject={canManageProject} isOwner={workspace.owner_id === me.id} onDeleted={() => { props.onWorkspace(""); props.onProject(""); props.onNavigate("home") }}/> : null}
      </div>
    </section>
    {composer ? <ComposerDialog type={composer} onClose={() => setComposer(null)} mutation={composer === "workspace" ? createWorkspace : createProject}/> : null}
    {taskId && project ? <TaskDialog taskId={taskId} project={project} canWrite={canManageProject || myProjectRole === "member"} onClose={() => props.onNavigate(view)} /> : null}
    {appError ? <button className="app-error" onClick={() => setAppError("")}><X/>{appError}</button> : null}
  </main>
}

function ProjectHeader({ project, view, navigate }: { project: Project; view: View; navigate: (view: View) => void }) {
  return <header className="project-header"><div className="project-title"><span style={{ background: project.color ?? "#579dff" }}>{project.key.slice(0, 2)}</span><div><small>{project.key}</small><h1>{project.name}</h1></div></div><nav aria-label={messages.app.navigationLabel}>{viewItems.map(({ id, label, icon: Icon }) => <button key={id} className={view === id ? "active" : ""} onClick={() => navigate(id)}><Icon/>{label}</button>)}</nav></header>
}

function GlobalHome({ workspace, projects, onProject, canManage, onCreate }: { workspace: Workspace; projects: Project[]; onProject: (id: string) => void; canManage: boolean; onCreate: () => void }) {
  const dashboard = useQuery({ queryKey: ["global-dashboard"], queryFn: api.globalDashboard })
  return <div className="home-view"><div className="page-heading"><div><p className="eyebrow">{workspace.name}</p><h1>{m.dashboard.global}</h1><p>{workspace.description}</p></div>{canManage ? <button className="primary" onClick={onCreate}><Plus/>{m.workspace.newProject}</button> : null}</div>
    <MetricGrid values={dashboard.data ? [{ label: m.dashboard.projects, value: dashboard.data.data.projects }, { label: m.dashboard.tasks, value: dashboard.data.data.tasks }, { label: m.dashboard.completed, value: dashboard.data.data.completed }, { label: m.dashboard.overdue, value: dashboard.data.data.overdue }] : []} loading={dashboard.isPending}/>
    <section className="content-section"><div className="section-heading"><h2>{m.workspace.projects}</h2></div><div className="project-grid">{projects.map((project) => <button className="project-tile" key={project.id} onClick={() => onProject(project.id)}><div className="project-cover" style={{ background: `linear-gradient(135deg, ${project.color ?? "#0c66e4"}, #101729)` }}><span>{project.key}</span></div><h3>{project.name}</h3><p>{project.description ?? m.project.overview}</p></button>)}</div></section>
  </div>
}

function Board({ project, search, canWrite, onTask }: { project: Project; search: string; canWrite: boolean; onTask: (id: string) => void }) {
  const client = useQueryClient()
  const [showArchived, setShowArchived] = useState(false)
  const columns = useQuery({ queryKey: ["columns", project.id], queryFn: () => api.columns(project.id) })
  const tasks = useQuery({ queryKey: ["tasks", project.id, "all"], queryFn: () => api.tasks(project.id, "", true), staleTime: 15_000 })
  const labels = useQuery({ queryKey: ["labels", project.id], queryFn: () => api.labels(project.id) })
  const create = useMutation({ mutationFn: ({ columnId, title }: { columnId: string; title: string }) => api.createTask(project.id, { column_id: columnId, title, priority: "medium" }), onSuccess: () => client.invalidateQueries({ queryKey: ["tasks", project.id] }) })
  const createColumn = useMutation({ mutationFn: (name: string) => api.createColumn(project.id, { name, is_done: false }), onSuccess: () => client.invalidateQueries({ queryKey: ["columns", project.id] }) })
  const updateColumn = useMutation({ mutationFn: ({ columnId, name }: { columnId: string; name: string }) => api.updateColumn(project.id, columnId, { name }), onSuccess: () => client.invalidateQueries({ queryKey: ["columns", project.id] }) })
  const archiveColumn = useMutation({ mutationFn: (columnId: string) => api.archiveColumn(project.id, columnId), onSuccess: () => client.invalidateQueries({ queryKey: ["columns", project.id] }) })
  const reorderColumns = useMutation({ mutationFn: (columnIds: string[]) => api.reorderColumns(project.id, { column_ids: columnIds }), onSuccess: () => client.invalidateQueries({ queryKey: ["columns", project.id] }) })
  const move = useMutation({
    mutationFn: ({ task, columnId, index }: { task: Task; columnId: string; index?: number }) => api.moveTask(task.id, { target_column_id: columnId, target_index: index ?? (tasks.data?.data.filter((item) => item.column_id === columnId && !item.archived_at).length ?? 0), version: task.version }),
    onMutate: async ({ task, columnId, index }) => {
      const queryKey = ["tasks", project.id, "all"] as const
      await client.cancelQueries({ queryKey })
      const snapshot = client.getQueryData<typeof tasks.data>(queryKey)
      client.setQueryData<typeof tasks.data>(queryKey, (value) => {
        if (!value) return value
        const remaining = value.data.filter((item) => item.id !== task.id)
        const targets = remaining.map((item, itemIndex) => ({ item, itemIndex })).filter(({ item }) => item.column_id === columnId && !item.archived_at)
        const targetIndex = index === undefined ? targets.length : Math.min(index, targets.length)
        const insertAt = targetIndex < targets.length ? targets[targetIndex].itemIndex : targets.length ? targets[targets.length - 1].itemIndex + 1 : remaining.length
        remaining.splice(insertAt, 0, { ...task, column_id: columnId })
        return { ...value, data: remaining }
      })
      return { snapshot, queryKey }
    },
    onError: (_error, _variables, context) => client.setQueryData(context?.queryKey ?? ["tasks", project.id, "all"], context?.snapshot),
    onSettled: () => client.invalidateQueries({ queryKey: ["tasks", project.id] }),
  })
  if (columns.isPending || tasks.isPending) return <InlineLoader/>
  if (columns.isError || tasks.isError) return <ErrorState error={columns.error ?? tasks.error} retry={() => { columns.refetch(); tasks.refetch() }}/>
  const reorder = (columnId: string, direction: -1 | 1) => {
    const ordered = [...columns.data.data]
    const currentIndex = ordered.findIndex((column) => column.id === columnId)
    const targetIndex = currentIndex + direction
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= ordered.length) return
    ;[ordered[currentIndex], ordered[targetIndex]] = [ordered[targetIndex], ordered[currentIndex]]
    reorderColumns.mutate(ordered.map((column) => column.id))
  }
  const filtered = tasks.data.data.filter((task) => (showArchived || !task.archived_at) && task.title.toLocaleLowerCase("fa").includes(search.toLocaleLowerCase("fa")))
  return <>{create.isError ? <ErrorNote error={create.error}/> : null}{move.isError ? <ErrorNote error={move.error}/> : null}{createColumn.isError || updateColumn.isError || archiveColumn.isError || reorderColumns.isError ? <ErrorNote error={createColumn.error ?? updateColumn.error ?? archiveColumn.error ?? reorderColumns.error}/> : null}<div className="view-toolbar"><button className={showArchived ? "ghost active" : "ghost"} onClick={() => setShowArchived((value) => !value)}><Archive/>{m.task.showArchived}</button><small>{m.task.dragHint}</small></div><div className="board-surface" aria-label={messages.board.columnsLabel}>{columns.data.data.map((column) => <BoardColumn key={column.id} column={column} columns={columns.data.data} tasks={filtered.filter((task) => task.column_id === column.id)} labels={labels.data?.data ?? []} canWrite={canWrite} onCreate={(title) => create.mutate({ columnId: column.id, title })} onMove={(task, id, index) => move.mutate({ task, columnId: id, index })} onRename={(name) => updateColumn.mutate({ columnId: column.id, name })} onReorder={(direction) => reorder(column.id, direction)} onArchive={() => archiveColumn.mutate(column.id)} onTask={onTask}/>)}</div>{canWrite ? <NewBoardColumn onCreate={(name) => createColumn.mutate(name)} pending={createColumn.isPending}/> : null}</>
}

function NewBoardColumn({ onCreate, pending }: { onCreate: (name: string) => void; pending: boolean }) {
  const [name, setName] = useState("")
  return <form className="new-column-card" onSubmit={(event) => { event.preventDefault(); const value = name.trim(); if (value) { onCreate(value); setName("") } }}><input value={name} onChange={(event) => setName(event.target.value)} placeholder={m.project.columnName} aria-label={m.project.columnName}/><button className="ghost" disabled={!name.trim() || pending}><Plus/>{m.project.addColumnOnBoard}</button></form>
}

function BoardColumn({ column, columns, tasks, canWrite, onCreate, onMove, onRename, onReorder, onArchive, onTask }: { column: Column; columns: Column[]; tasks: Task[]; labels: unknown[]; canWrite: boolean; onCreate: (title: string) => void; onMove: (task: Task, id: string, index?: number) => void; onRename: (name: string) => void; onReorder: (direction: -1 | 1) => void; onArchive: () => void; onTask: (id: string) => void }) {
  const [title, setTitle] = useState("")
  const [menuOpen, setMenuOpen] = useState(false)
  const draggedTask = (event: DragEvent) => { try { return JSON.parse(event.dataTransfer.getData("application/json")) as Task } catch { return null } }
  const rename = () => { const name = window.prompt(m.project.renameColumnPrompt, column.name)?.trim(); if (name && name !== column.name) onRename(name); setMenuOpen(false) }
  const archive = () => { if (window.confirm(m.project.archiveColumnConfirm)) onArchive(); setMenuOpen(false) }
  return <article className="trello-list" onDragOver={(event) => { if (canWrite) event.preventDefault() }} onDrop={(event) => { event.preventDefault(); const task = draggedTask(event); if (task) onMove(task, column.id) }}><header><div><span className={column.is_done ? "status-dot done" : "status-dot"}/><h2>{column.name}</h2></div><div><span className="count">{tasks.length}</span>{canWrite ? <div className="column-menu-wrap"><button className="icon-button" aria-label={m.project.columnActions} aria-expanded={menuOpen} onClick={() => setMenuOpen((value) => !value)}><MoreHorizontal/></button>{menuOpen ? <div className="column-menu" role="menu"><button role="menuitem" onClick={rename}><Pencil/>{m.project.renameColumn}</button><button role="menuitem" onClick={() => { onReorder(-1); setMenuOpen(false) }} disabled={columns[0]?.id === column.id}><ArrowUp/>{m.project.moveUp}</button><button role="menuitem" onClick={() => { onReorder(1); setMenuOpen(false) }} disabled={columns[columns.length - 1]?.id === column.id}><ArrowDown/>{m.project.moveDown}</button><button role="menuitem" className="danger-action" onClick={archive}><Archive/>{m.project.archiveColumn}</button></div> : null}</div> : null}</div></header><div className="card-stack">{tasks.map((task, index) => <article key={task.id} draggable={canWrite && !task.archived_at} className={`trello-card ${task.archived_at ? "archived" : ""}`} tabIndex={0} onDragStart={(event) => { event.dataTransfer.setData("application/json", JSON.stringify(task)); event.dataTransfer.effectAllowed = "move" }} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.stopPropagation(); event.preventDefault(); const dragged = draggedTask(event); if (dragged) onMove(dragged, column.id, index) }} onClick={() => onTask(task.id)} onKeyDown={(event) => { if (event.key === "Enter") onTask(task.id) }}><span className={`label-bar ${task.priority}`}/><h3>{task.title}</h3><div className="card-meta">{task.due_at ? <span className={new Date(task.due_at) < new Date() ? "late" : ""}><Clock3/>{dateText(task.due_at)}</span> : null}{task.archived_at ? <span><Archive/>{m.task.archive}</span> : null}<span className="task-id">{task.id.slice(0, 4)}</span></div>{canWrite && !task.archived_at ? <select aria-label={m.task.move} value={task.column_id} onClick={(event) => event.stopPropagation()} onChange={(event) => onMove(task, event.target.value)}>{columns.map((target) => <option value={target.id} key={target.id}>{target.name}</option>)}</select> : null}</article>)}</div>{canWrite ? <form className="card-composer" onSubmit={(event) => { event.preventDefault(); if (title.trim()) { onCreate(title.trim()); setTitle("") } }}><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={m.task.add}/><button disabled={!title.trim()}><Plus/></button></form> : null}</article>
}

function TaskList({ project, search, onTask }: { project: Project; search: string; onTask: (id: string) => void }) {
  const [showArchived, setShowArchived] = useState(false)
  const tasks = useQuery({ queryKey: ["tasks", project.id, "all"], queryFn: () => api.tasks(project.id, "", true) })
  const columns = useQuery({ queryKey: ["columns", project.id], queryFn: () => api.columns(project.id) })
  const columnMap = useMemo(() => new Map(columns.data?.data.map((item) => [item.id, item.name])), [columns.data])
  if (tasks.isPending || columns.isPending) return <InlineLoader/>
  const rows = tasks.data?.data.filter((task) => (showArchived || !task.archived_at) && task.title.includes(search)) ?? []
  return <section className="table-panel"><div className="view-toolbar"><button className={showArchived ? "ghost active" : "ghost"} onClick={() => setShowArchived((value) => !value)}><Archive/>{m.task.showArchived}</button></div><table><thead><tr><th>{m.task.title}</th><th>{m.task.priority}</th><th>{m.task.due}</th><th>{m.nav.board}</th></tr></thead><tbody>{rows.map((task) => <tr className={task.archived_at ? "archived" : ""} key={task.id} onClick={() => onTask(task.id)}><td>{task.archived_at ? <Archive/> : <Circle/>}{task.title}</td><td><span className={`priority-pill ${task.priority}`}>{messages.board.priorities[task.priority]}</span></td><td>{dateText(task.due_at)}</td><td>{columnMap.get(task.column_id)}</td></tr>)}</tbody></table>{!rows.length ? <EmptyState text={m.noData}/> : null}</section>
}

function DateView({ project, mode }: { project: Project; mode: "timeline" | "calendar" }) {
  const now = new Date(); const start = new Date(now.getFullYear(), now.getMonth() - 1, 1).toISOString(); const end = new Date(now.getFullYear(), now.getMonth() + 2, 0).toISOString()
  const query = useQuery({ queryKey: [mode, project.id, start, end], queryFn: () => mode === "timeline" ? api.timeline(project.id, start, end) : api.calendar(project.id, start, end) })
  if (query.isPending) return <InlineLoader/>
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()}/>
  if (mode === "timeline") return <section className="timeline-panel"><div className="timeline-axis"><span>{dateText(start)}</span><span>{dateText(now.toISOString())}</span><span>{dateText(end)}</span></div>{query.data.data.map((task) => { const geometry = timelineGeometry(task, start, end); return <div className="timeline-row" key={task.id}><span>{task.title}</span><div><i style={{ insetInlineStart: `${geometry.left}%`, width: `${geometry.width}%` }} className={task.priority}/></div><small>{dateText(task.due_at)}</small></div> })}</section>
  const grouped = Map.groupBy(query.data.data, (task) => task.due_at?.slice(0, 10) ?? "none")
  return <section className="calendar-panel"><div className="calendar-grid">{Array.from({ length: 35 }, (_, index) => { const day = new Date(now.getFullYear(), now.getMonth(), index - 2); const key = day.toISOString().slice(0, 10); return <article key={key}><span>{new Intl.NumberFormat("fa-IR").format(day.getDate())}</span>{(grouped.get(key) ?? []).map((task) => <div className={task.priority} key={task.id}>{task.title}</div>)}</article> })}</div></section>
}

function ProjectDashboard({ project }: { project: Project }) {
  const dashboard = useQuery({ queryKey: ["project-dashboard", project.id], queryFn: () => api.projectDashboard(project.id) })
  const activity = useQuery({ queryKey: ["project-activity", project.id], queryFn: () => api.projectActivity(project.id) })
  if (dashboard.isPending) return <InlineLoader/>
  if (dashboard.isError) return <ErrorState error={dashboard.error} retry={() => dashboard.refetch()}/>
  const data = dashboard.data.data
  return <div className="dashboard-view"><MetricGrid values={[{ label: m.dashboard.tasks, value: data.total }, { label: m.dashboard.completed, value: data.completed }, { label: m.dashboard.overdue, value: data.overdue }, { label: m.dashboard.dueSoon, value: data.due_soon }, { label: m.dashboard.unassigned, value: data.unassigned }]}/><div className="dashboard-columns"><section className="chart-panel"><h2>{m.dashboard.byPriority}</h2><div className="bar-chart">{Object.entries(data.by_priority).map(([label, value]) => <div key={label}><span>{messages.board.priorities[label as keyof typeof messages.board.priorities] ?? label}</span><i><b style={{ width: `${data.total ? Math.max(5, value / data.total * 100) : 0}%` }}/></i><strong>{value}</strong></div>)}</div><p className="chart-summary"><b>{m.dashboard.textSummary}:</b> {Object.entries(data.by_priority).map(([key, value]) => `${key}: ${value}`).join("، ")}</p></section><ActivityPanel items={activity.data?.data ?? []}/></div></div>
}

function Members({ workspace, project, canManageWorkspace, canManageProject }: { workspace: Workspace; project?: Project; canManageWorkspace: boolean; canManageProject: boolean }) {
  const client = useQueryClient(); const [tab, setTab] = useState<"workspace" | "project">("workspace")
  const members = useQuery({ queryKey: ["workspace-members", workspace.id], queryFn: () => api.workspaceMembers(workspace.id) })
  const invitations = useQuery({ queryKey: ["invitations", workspace.id], queryFn: () => api.invitations(workspace.id), enabled: canManageWorkspace })
  const projectMembers = useQuery({ queryKey: ["project-members", project?.id], queryFn: () => api.projectMembers(project!.id), enabled: Boolean(project) })
  const invite = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.invite(workspace.id, { email: String(data.get("email")), role: String(data.get("role")) as "OWNER" | "ADMIN" | "PROJECT_MANAGER" | "MEMBER" }) }, onSuccess: () => client.invalidateQueries({ queryKey: ["invitations", workspace.id] }) })
  const addProject = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.addProjectMember(project!.id, { user_id: String(data.get("userId")), role: "member" }) }, onSuccess: () => client.invalidateQueries({ queryKey: ["project-members", project?.id] }) })
  const data = tab === "workspace" ? members.data?.data : projectMembers.data?.data
  const canManageCurrent = tab === "workspace" ? canManageWorkspace : canManageProject
  const refreshMembers = () => client.invalidateQueries({ queryKey: [tab === "workspace" ? "workspace-members" : "project-members", tab === "workspace" ? workspace.id : project?.id] })
  return <div className="admin-view">{invite.isError ? <ErrorNote error={invite.error}/> : null}{addProject.isError ? <ErrorNote error={addProject.error}/> : null}<div className="segmented compact"><button className={tab === "workspace" ? "active" : ""} onClick={() => setTab("workspace")}>{m.member.workspaceMembers}</button><button className={tab === "project" ? "active" : ""} onClick={() => setTab("project")}>{m.member.projectMembers}</button></div><section className="admin-card"><h2>{tab === "workspace" ? m.member.workspaceMembers : m.member.projectMembers}</h2><div className="member-list">{data?.map((member) => <article key={member.id}><span className="avatar small">{initials(member.user.name)}</span><div><b>{member.user.name}</b><small dir="ltr">{member.user.email}</small><small>{m.member.joined}: {dateText(member.joined_at)}</small></div>{canManageCurrent ? <><select className="role-select" aria-label={m.member.changeRole} value={member.role} onChange={(event) => { const role = event.target.value; const call = tab === "workspace" ? api.updateWorkspaceMember(workspace.id, member.id, { role: role as "OWNER" | "ADMIN" | "PROJECT_MANAGER" | "MEMBER" }) : api.updateProjectMember(project!.id, member.id, { role: role as "manager" | "member" }); void call.then(refreshMembers) }}>{tab === "workspace" ? <><option value="OWNER">OWNER</option><option value="ADMIN">ADMIN</option><option value="PROJECT_MANAGER">PROJECT_MANAGER</option><option value="MEMBER">MEMBER</option></> : <><option value="manager">manager</option><option value="member">member</option></>}</select><button className="text-danger" onClick={() => { const call = tab === "workspace" ? api.removeWorkspaceMember(workspace.id, member.id) : api.removeProjectMember(project!.id, member.id); void call.then(refreshMembers) }}>{m.member.remove}</button></> : <span className="role-badge">{member.role}</span>}</article>)}</div></section>{tab === "workspace" && canManageWorkspace ? <section className="admin-card"><h2>{m.member.invite}</h2><form className="inline-form" onSubmit={(event) => { event.preventDefault(); invite.mutate(event.currentTarget); event.currentTarget.reset() }}><Field name="email" label={m.member.email} type="email"/><label><span>{m.member.role}</span><select name="role"><option value="MEMBER">MEMBER</option><option value="PROJECT_MANAGER">PROJECT_MANAGER</option><option value="ADMIN">ADMIN</option></select></label><button className="primary">{m.member.invite}</button></form>{invite.data ? <div className="invite-link"><code dir="ltr">{`${window.location.origin}/invite/${invite.data.data.token}`}</code><button className="ghost" onClick={() => void navigator.clipboard.writeText(`${window.location.origin}/invite/${invite.data.data.token}`)}>{m.member.copyInvite}</button></div> : null}<h3>{m.member.pendingInvites}</h3>{invitations.data?.data.map((item) => <div className="invite-row" key={item.id}><span>{item.email}</span><span>{item.role}</span><button onClick={() => void api.revokeInvitation(workspace.id, item.id).then(() => client.invalidateQueries({ queryKey: ["invitations", workspace.id] }))}>{m.member.revoke}</button></div>)}</section> : null}{tab === "project" && project && canManageProject ? <section className="admin-card"><h2>{m.member.projectMembers}</h2><form className="inline-form" onSubmit={(event) => { event.preventDefault(); addProject.mutate(event.currentTarget); event.currentTarget.reset() }}><Field name="userId" label={m.member.userId} dir="ltr"/><button className="primary">{m.member.invite}</button></form></section> : null}{!canManageWorkspace && !canManageProject ? <p className="permission-note">{m.member.readOnly}</p> : null}</div>
}

function SettingsView({ workspace, project, canManageWorkspace, canManageProject, isOwner, onDeleted }: { workspace: Workspace; project?: Project; canManageWorkspace: boolean; canManageProject: boolean; isOwner: boolean; onDeleted: () => void }) {
  const client = useQueryClient(); const ws = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.updateWorkspace(workspace.id, { name: String(data.get("name")), description: String(data.get("description")) }) }, onSuccess: () => client.invalidateQueries({ queryKey: ["workspaces"] }) }); const pr = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.updateProject(project!.id, { name: String(data.get("name")), description: String(data.get("description")) }) }, onSuccess: () => client.invalidateQueries({ queryKey: ["projects", workspace.id] }) })
  return <div className="settings-grid"><section className="admin-card"><h2>{m.workspace.settings}</h2><form onSubmit={(event) => { event.preventDefault(); ws.mutate(event.currentTarget) }}><Field name="name" label={m.workspace.name} defaultValue={workspace.name} disabled={!canManageWorkspace}/><TextArea name="description" label={m.workspace.description} defaultValue={workspace.description ?? ""} disabled={!canManageWorkspace}/>{canManageWorkspace ? <div className="form-actions"><button className="primary">{m.save}</button><button type="button" className="danger" onClick={() => void api.archiveWorkspace(workspace.id, Boolean(workspace.archived_at)).then(() => client.invalidateQueries({ queryKey: ["workspaces"] }))}>{workspace.archived_at ? <RotateCcw/> : <Archive/>}{workspace.archived_at ? m.workspace.restore : m.workspace.archive}</button>{isOwner ? <button type="button" className="danger permanent" onClick={() => { const confirmation = window.prompt(m.workspace.deleteConfirm); if (confirmation === workspace.name) void api.deleteWorkspace(workspace.id).then(() => { client.invalidateQueries({ queryKey: ["workspaces"] }); onDeleted() }) }}>{m.workspace.permanentDelete}</button> : null}</div> : <p className="permission-note">{m.member.readOnly}</p>}</form></section>{project ? <section className="admin-card"><h2>{m.project.edit}</h2><form onSubmit={(event) => { event.preventDefault(); pr.mutate(event.currentTarget) }}><Field name="name" label={m.workspace.projectName} defaultValue={project.name} disabled={!canManageProject}/><TextArea name="description" label={m.workspace.description} defaultValue={project.description ?? ""} disabled={!canManageProject}/>{canManageProject ? <div className="form-actions"><button className="primary">{m.save}</button><button type="button" className="danger" onClick={() => void api.archiveProject(project.id, Boolean(project.archived_at)).then(() => client.invalidateQueries({ queryKey: ["projects", workspace.id] }))}>{project.archived_at ? <RotateCcw/> : <Archive/>}{project.archived_at ? m.project.restore : m.project.archive}</button></div> : null}</form></section> : null}{project ? <ProjectResources project={project} canManage={canManageProject}/> : null}</div>
}

function ProjectResources({ project, canManage }: { project: Project; canManage: boolean }) {
  const client = useQueryClient(); const columns = useQuery({ queryKey: ["columns", project.id], queryFn: () => api.columns(project.id) }); const labels = useQuery({ queryKey: ["labels", project.id], queryFn: () => api.labels(project.id) })
  const refreshColumns = () => client.invalidateQueries({ queryKey: ["columns", project.id] }); const refreshLabels = () => client.invalidateQueries({ queryKey: ["labels", project.id] })
  const reorder = (index: number, direction: -1 | 1) => { const ordered = [...(columns.data?.data ?? [])]; const target = index + direction; if (target < 0 || target >= ordered.length) return; [ordered[index], ordered[target]] = [ordered[target], ordered[index]]; void api.reorderColumns(project.id, { column_ids: ordered.map((column) => column.id) }).then(refreshColumns) }
  return <><section className="admin-card"><h2>{m.project.columns}</h2><div className="resource-list">{columns.data?.data.map((column, index) => <div key={column.id}>{canManage ? <span className="reorder-actions"><button disabled={index === 0} onClick={() => reorder(index, -1)} aria-label={m.project.moveUp}><ArrowUp/></button><button disabled={index === (columns.data?.data.length ?? 0) - 1} onClick={() => reorder(index, 1)} aria-label={m.project.moveDown}><ArrowDown/></button></span> : null}<input defaultValue={column.name} disabled={!canManage} onBlur={(event) => { if (event.target.value !== column.name) void api.updateColumn(project.id, column.id, { name: event.target.value }).then(refreshColumns) }}/><label><input type="checkbox" checked={column.is_done} disabled={!canManage} onChange={() => void api.updateColumn(project.id, column.id, { is_done: !column.is_done }).then(refreshColumns)}/><Check/>{m.dashboard.completed}</label>{canManage ? <button className="text-danger" onClick={() => void api.archiveColumn(project.id, column.id).then(refreshColumns)}>{m.task.remove}</button> : null}</div>)}</div>{canManage ? <form className="mini-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("column") as HTMLInputElement; if (input.value.trim()) void api.createColumn(project.id, { name: input.value.trim(), is_done: false }).then(() => { input.value = ""; refreshColumns() }) }}><input name="column" placeholder={m.project.columnName}/><button><Plus/>{m.project.addColumn}</button></form> : null}</section><section className="admin-card"><h2>{m.task.labels}</h2><div className="resource-list">{labels.data?.data.map((label) => <div key={label.id}><i style={{ background: label.color ?? "#579dff" }}/><input defaultValue={label.name} disabled={!canManage} onBlur={(event) => { if (event.target.value !== label.name) void api.updateLabel(label.id, { name: event.target.value }).then(refreshLabels) }}/>{canManage ? <button className="text-danger" onClick={() => void api.archiveLabel(label.id).then(refreshLabels)}>{m.task.remove}</button> : null}</div>)}</div>{canManage ? <form className="mini-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("label") as HTMLInputElement; if (input.value.trim()) void api.createLabel(project.id, { name: input.value.trim(), color: "#579dff" }).then(() => { input.value = ""; refreshLabels() }) }}><input name="label" placeholder={m.task.labelName}/><button><Plus/>{m.task.addLabel}</button></form> : null}</section></>
}

function Notifications({ onOpen }: { onOpen: (item: Notification) => Promise<void> }) {
  const client = useQueryClient(); const query = useQuery({ queryKey: ["notifications"], queryFn: api.notifications, refetchInterval: 30_000 })
  if (query.isPending) return <InlineLoader/>
  return <section className="notifications-view"><div className="page-heading"><div><p className="eyebrow">{m.nav.notifications}</p><h1>{m.notification.title}</h1></div><button className="ghost" onClick={() => void api.markAllNotifications().then(() => { client.invalidateQueries({ queryKey: ["notifications"] }); client.invalidateQueries({ queryKey: ["notification-count"] }) })}><Check/>{m.notification.markAll}</button></div><div className="notification-list">{query.data?.data.map((item) => <button key={item.id} className={item.read_at ? "" : "unread"} onClick={() => void api.markNotification(item.id).then(() => { client.invalidateQueries({ queryKey: ["notifications"] }); client.invalidateQueries({ queryKey: ["notification-count"] }); return onOpen(item) })}><span className="notification-icon"><Bell/></span><span><b>{item.title}</b><p>{item.body}</p><small>{dateText(item.created_at)}</small></span>{!item.read_at ? <i/> : null}</button>)}</div>{!query.data?.data.length ? <EmptyState text={m.notification.empty}/> : null}</section>
}

function Profile({ user, onUser }: { user: User; onUser: (user: User) => void }) {
  const client = useQueryClient()
  const avatar = useQuery({ queryKey: ["avatar", user.id, user.avatar_content_type], queryFn: async () => URL.createObjectURL(await api.avatar()), enabled: Boolean(user.avatar_content_type) })
  const update = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.updateProfile({ name: String(data.get("name")), timezone: String(data.get("timezone")) }) }, onSuccess: (result) => onUser(result.data) })
  useEffect(() => () => { if (avatar.data) URL.revokeObjectURL(avatar.data) }, [avatar.data])
  return <section className="profile-view"><div className="page-heading"><div><p className="eyebrow">{user.email}</p><h1>{m.profile.title}</h1></div></div><div className="profile-layout"><div className="profile-avatar"><span>{avatar.data ? <Image src={avatar.data} alt={user.name} width={96} height={96} unoptimized/> : initials(user.name)}</span><label className="ghost">{m.profile.upload}<input type="file" accept="image/png,image/jpeg" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void api.uploadAvatar(file).then((result) => { onUser(result.data); client.invalidateQueries({ queryKey: ["avatar", user.id] }) }) }}/></label><button className="text-button" onClick={() => void api.deleteAvatar().then(() => { onUser({ ...user, avatar_content_type: null }); client.removeQueries({ queryKey: ["avatar", user.id] }) })}>{m.profile.remove}</button></div><form className="admin-card" onSubmit={(event) => { event.preventDefault(); update.mutate(event.currentTarget) }}><Field name="name" label={m.auth.name} defaultValue={user.name}/><Field name="email" label={m.auth.email} defaultValue={user.email} disabled dir="ltr"/><label><span>{m.profile.timezone}</span><select name="timezone" defaultValue={user.timezone}><option value="Asia/Tehran">Asia/Tehran</option><option value="UTC">UTC</option><option value="Europe/London">Europe/London</option><option value="America/New_York">America/New_York</option></select></label><button className="primary">{m.save}</button></form></div></section>
}

function TaskDialog({ taskId, project, canWrite, onClose }: { taskId: string; project: Project; canWrite: boolean; onClose: () => void }) {
  const client = useQueryClient()
  const task = useQuery({ queryKey: ["task", taskId], queryFn: () => api.task(taskId) })
  const comments = useQuery({ queryKey: ["comments", taskId], queryFn: () => api.comments(taskId) })
  const checklists = useQuery({ queryKey: ["checklists", taskId], queryFn: () => api.checklists(taskId) })
  const attachments = useQuery({ queryKey: ["attachments", taskId], queryFn: () => api.attachments(taskId) })
  const activity = useQuery({ queryKey: ["activity", taskId], queryFn: () => api.activity(taskId) })
  const labels = useQuery({ queryKey: ["labels", project.id], queryFn: () => api.labels(project.id) })
  const members = useQuery({ queryKey: ["project-members", project.id], queryFn: () => api.projectMembers(project.id) })
  const memberMap = useMemo(() => new Map(members.data?.data.map((member) => [member.user_id, member.user])), [members.data])
  const invalidateTask = () => {
    void client.invalidateQueries({ queryKey: ["task", taskId] })
    void client.invalidateQueries({ queryKey: ["tasks", project.id] })
    void client.invalidateQueries({ queryKey: ["activity", taskId] })
  }
  const invalidateChecklists = () => void client.invalidateQueries({ queryKey: ["checklists", taskId] })
  const invalidateComments = () => void client.invalidateQueries({ queryKey: ["comments", taskId] })
  const update = useMutation({
    mutationFn: (form: HTMLFormElement) => {
      const data = new FormData(form)
      return api.updateTask(taskId, {
        title: String(data.get("title")),
        description: String(data.get("description")),
        priority: String(data.get("priority")) as Task["priority"],
        due_at: String(data.get("due")) ? new Date(String(data.get("due"))).toISOString() : null,
      })
    },
    onSuccess: invalidateTask,
  })
  const addComment = useMutation({ mutationFn: (body: string) => api.createComment(taskId, body), onSuccess: invalidateComments })
  if (task.isPending) return <Dialog onClose={onClose}><InlineLoader/></Dialog>
  if (task.isError) return <Dialog onClose={onClose}><ErrorState error={task.error} retry={() => task.refetch()}/></Dialog>
  const data = task.data.data
  return <Dialog onClose={onClose} className="task-dialog">
    <div className="task-main">
      <div className="task-context"><span>{project.name}</span><ChevronDown/></div>
      <form onSubmit={(event) => { event.preventDefault(); update.mutate(event.currentTarget) }}>
        <input className="task-title-input" name="title" defaultValue={data.title} disabled={!canWrite}/>
        <div className="task-toolbar">
          <label><Clock3/><span>{m.task.due}</span><input name="due" type="date" defaultValue={data.due_at?.slice(0, 10)} disabled={!canWrite}/></label>
          <label><ChartNoAxesCombined/><span>{m.task.priority}</span><select name="priority" defaultValue={data.priority} disabled={!canWrite}>{priorities.map((priority) => <option key={priority} value={priority}>{messages.board.priorities[priority]}</option>)}</select></label>
          <label><Users/><span>{m.task.assignees}</span><select disabled={!canWrite} defaultValue="" onChange={(event) => { if (event.target.value) void api.addAssignee(taskId, event.target.value).then(invalidateTask) }}><option value="">+</option>{members.data?.data.map((member) => <option key={member.user_id} value={member.user_id}>{member.user.name}</option>)}</select></label>
          <label><span className="label-icon"/><span>{m.task.labels}</span><select disabled={!canWrite} defaultValue="" onChange={(event) => { if (event.target.value) void api.addTaskLabel(taskId, event.target.value).then(invalidateTask) }}><option value="">+</option>{labels.data?.data.map((label) => <option key={label.id} value={label.id}>{label.name}</option>)}</select></label>
        </div>
        <div className="association-chips">
          {data.assignees.map((assignee) => <span key={assignee.user_id}><Users/>{memberMap.get(assignee.user_id)?.name ?? assignee.user_id.slice(0, 8)}{canWrite ? <button type="button" onClick={() => void api.removeAssignee(taskId, assignee.user_id).then(invalidateTask)}><X/></button> : null}</span>)}
          {data.task_labels.map((taskLabel) => <span key={taskLabel.label_id} style={{ borderColor: taskLabel.label.color ?? "#579dff" }}>{taskLabel.label.name}{canWrite ? <button type="button" onClick={() => void api.removeTaskLabel(taskId, taskLabel.label_id).then(invalidateTask)}><X/></button> : null}</span>)}
        </div>
        <section className="task-section"><h2>{m.task.description}</h2><textarea name="description" defaultValue={data.description ?? ""} disabled={!canWrite}/></section>
        {update.isError ? <ErrorNote error={update.error}/> : null}
        {canWrite ? <button className="primary">{m.save}</button> : null}
      </form>
      <section className="task-section">
        <div className="section-heading"><h2>{m.task.subtask}</h2></div>
        {data.subtasks.map((subtask) => <div className="subtask-row" key={subtask.id}><Circle/><span>{subtask.title}</span><small>{messages.board.priorities[subtask.priority]}</small></div>)}
        {canWrite ? <form className="mini-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("subtask") as HTMLInputElement; if (input.value.trim()) void api.createSubtask(taskId, { title: input.value.trim(), column_id: data.column_id, priority: "medium" }).then(() => { input.value = ""; invalidateTask() }) }}><input name="subtask" placeholder={m.task.addSubtask}/><button><Plus/></button></form> : null}
      </section>
      <section className="task-section">
        <div className="section-heading"><h2><CheckCircle2/>{m.task.checklist}</h2>{canWrite ? <button className="ghost" onClick={() => { const title = window.prompt(m.task.addChecklist); if (title) void api.createChecklist(taskId, title).then(invalidateChecklists) }}><Plus/>{m.task.addChecklist}</button> : null}</div>
        {checklists.data?.data.map((list) => <div className="checklist" key={list.id}>
          <div className="checklist-head"><input className="checklist-title" defaultValue={list.title} disabled={!canWrite} onBlur={(event) => { const title = event.target.value.trim(); if (title && title !== list.title) void api.updateChecklist(list.id, title).then(invalidateChecklists) }}/><span>{list.completed_items}/{list.total_items}</span>{canWrite ? <button className="text-danger" onClick={() => void api.deleteChecklist(list.id).then(invalidateChecklists)}>{m.task.remove}</button> : null}</div>
          <progress value={list.completed_items} max={Math.max(1, list.total_items)}/>
          {list.items.map((item, index) => <label key={item.id}><input type="checkbox" checked={item.completed} disabled={!canWrite} onChange={() => void api.updateChecklistItem(item.id, { completed: !item.completed }).then(invalidateChecklists)}/><span>{item.title}</span>{canWrite ? <span className="reorder-actions"><button type="button" disabled={index === 0} onClick={() => { const ids = list.items.map((entry) => entry.id); [ids[index - 1], ids[index]] = [ids[index], ids[index - 1]]; void api.reorderChecklistItems(list.id, ids).then(invalidateChecklists) }}><ArrowUp/></button><button type="button" disabled={index === list.items.length - 1} onClick={() => { const ids = list.items.map((entry) => entry.id); [ids[index], ids[index + 1]] = [ids[index + 1], ids[index]]; void api.reorderChecklistItems(list.id, ids).then(invalidateChecklists) }}><ArrowDown/></button><button type="button" className="text-danger" onClick={() => void api.deleteChecklistItem(item.id).then(invalidateChecklists)}><X/></button></span> : null}</label>)}
          {canWrite ? <form className="mini-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("item") as HTMLInputElement; if (input.value.trim()) void api.addChecklistItem(list.id, input.value.trim()).then(() => { input.value = ""; invalidateChecklists() }) }}><input name="item" placeholder={m.task.addItem}/><button><Plus/></button></form> : null}
        </div>)}
      </section>
      <section className="task-section">
        <div className="section-heading"><h2><Paperclip/>{m.task.attachment}</h2>{canWrite ? <label className="ghost">{m.task.upload}<input hidden type="file" onChange={(event) => { const file = event.target.files?.[0]; if (file) void api.uploadAttachment(taskId, file).then(() => client.invalidateQueries({ queryKey: ["attachments", taskId] })) }}/></label> : null}</div>
        <div className="attachment-list">{attachments.data?.data.map((file) => <div key={file.id}><button className="attachment-download" onClick={() => void saveAttachment(file.id, file.original_name)}><Paperclip/><span>{file.original_name}</span><small>{Math.ceil(file.size_bytes / 1024)} KB</small><b>{m.task.download}</b></button>{canWrite ? <button className="text-danger" onClick={() => void api.deleteAttachment(file.id).then(() => client.invalidateQueries({ queryKey: ["attachments", taskId] }))}>{m.task.remove}</button> : null}</div>)}</div>
      </section>
      {canWrite ? <button className="danger" onClick={() => void api.archiveTask(taskId, Boolean(data.archived_at)).then(() => { invalidateTask(); onClose() })}>{data.archived_at ? <RotateCcw/> : <Archive/>}{data.archived_at ? m.task.restore : m.task.archive}</button> : null}
    </div>
    <aside className="task-activity">
      <div className="activity-title"><MessageSquare/><h2>{m.task.commentsActivity}</h2></div>
      <form className="comment-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("comment") as HTMLInputElement; if (input.value.trim()) { addComment.mutate(input.value.trim()); input.value = "" } }}><input name="comment" placeholder={m.task.commentPlaceholder} disabled={!canWrite}/><button disabled={!canWrite}>{m.task.sendComment}</button></form>
      <div className="comment-list">{comments.data?.data.map((comment) => <article key={comment.id}><span className="avatar small">{comment.author_id.slice(0, 2)}</span><div><b>{comment.author_id.slice(0, 8)}</b><p>{comment.body}</p><small>{dateText(comment.created_at)}</small>{canWrite ? <span className="comment-actions"><button onClick={() => { const body = window.prompt(m.task.edit, comment.body); if (body?.trim() && body.trim() !== comment.body) void api.updateComment(comment.id, body.trim()).then(invalidateComments) }}>{m.task.edit}</button><button className="text-danger" onClick={() => void api.deleteComment(comment.id).then(invalidateComments)}>{m.task.remove}</button></span> : null}</div></article>)}{!comments.data?.data.length ? <p className="empty-copy">{m.task.noComments}</p> : null}</div>
      <ActivityPanel items={activity.data?.data ?? []}/>
    </aside>
  </Dialog>
}

/* Previous single-line task dialog retained temporarily for migration reference.
function TaskDialogLegacy({ taskId, project, canWrite, onClose }: { taskId: string; project: Project; canWrite: boolean; onClose: () => void }) {
  const client = useQueryClient(); const task = useQuery({ queryKey: ["task", taskId], queryFn: () => api.task(taskId) }); const comments = useQuery({ queryKey: ["comments", taskId], queryFn: () => api.comments(taskId) }); const checklists = useQuery({ queryKey: ["checklists", taskId], queryFn: () => api.checklists(taskId) }); const attachments = useQuery({ queryKey: ["attachments", taskId], queryFn: () => api.attachments(taskId) }); const activity = useQuery({ queryKey: ["activity", taskId], queryFn: () => api.activity(taskId) }); const labels = useQuery({ queryKey: ["labels", project.id], queryFn: () => api.labels(project.id) }); const members = useQuery({ queryKey: ["project-members", project.id], queryFn: () => api.projectMembers(project.id) })
  const invalidate = () => { client.invalidateQueries({ queryKey: ["task", taskId] }); client.invalidateQueries({ queryKey: ["tasks", project.id] }); client.invalidateQueries({ queryKey: ["activity", taskId] }) }
  const update = useMutation({ mutationFn: (form: HTMLFormElement) => { const data = new FormData(form); return api.updateTask(taskId, { title: String(data.get("title")), description: String(data.get("description")), priority: String(data.get("priority")) as Task["priority"], due_at: String(data.get("due")) ? new Date(String(data.get("due"))).toISOString() : null }) }, onSuccess: invalidate })
  const addComment = useMutation({ mutationFn: (body: string) => api.createComment(taskId, body), onSuccess: () => { client.invalidateQueries({ queryKey: ["comments", taskId] }); client.invalidateQueries({ queryKey: ["activity", taskId] }) } })
  if (task.isPending) return <Dialog onClose={onClose}><InlineLoader/></Dialog>
  if (task.isError) return <Dialog onClose={onClose}><ErrorState error={task.error} retry={() => task.refetch()}/></Dialog>
  const data = task.data.data
  return <Dialog onClose={onClose} className="task-dialog"><div className="task-main"><div className="task-context"><span>{project.name}</span><ChevronDown/></div><form onSubmit={(event) => { event.preventDefault(); update.mutate(event.currentTarget) }}><input className="task-title-input" name="title" defaultValue={data.title} disabled={!canWrite}/><div className="task-toolbar"><label><Clock3/><span>{m.task.due}</span><input name="due" type="date" defaultValue={data.due_at?.slice(0, 10)} disabled={!canWrite}/></label><label><ChartNoAxesCombined/><span>{m.task.priority}</span><select name="priority" defaultValue={data.priority} disabled={!canWrite}>{priorities.map((priority) => <option key={priority} value={priority}>{messages.board.priorities[priority]}</option>)}</select></label><label><Users/><span>{m.task.assignees}</span><select disabled={!canWrite} defaultValue="" onChange={(event) => { if (event.target.value) void api.addAssignee(taskId, event.target.value).then(invalidate) }}><option value="">+</option>{members.data?.data.map((member) => <option key={member.user_id} value={member.user_id}>{member.user_id.slice(0, 8)}</option>)}</select></label><label><span className="label-icon"/><span>{m.task.labels}</span><select disabled={!canWrite} defaultValue="" onChange={(event) => { if (event.target.value) void api.addTaskLabel(taskId, event.target.value).then(invalidate) }}><option value="">+</option>{labels.data?.data.map((label) => <option key={label.id} value={label.id}>{label.name}</option>)}</select></label></div><div className="association-chips">{data.assignees.map((assignee) => <span key={assignee.user_id}><Users/>{assignee.user_id.slice(0, 8)}{canWrite ? <button type="button" onClick={() => void api.removeAssignee(taskId, assignee.user_id).then(invalidate)}><X/></button> : null}</span>)}{data.task_labels.map((taskLabel) => <span key={taskLabel.label_id} style={{ borderColor: taskLabel.label.color ?? "#579dff" }}>{taskLabel.label.name}{canWrite ? <button type="button" onClick={() => void api.removeTaskLabel(taskId, taskLabel.label_id).then(invalidate)}><X/></button> : null}</span>)}</div><section className="task-section"><h2>{m.task.description}</h2><textarea name="description" defaultValue={data.description ?? ""} disabled={!canWrite} placeholder={m.task.description}/></section>{canWrite ? <button className="primary">{m.save}</button> : null}</form><section className="task-section"><div className="section-heading"><h2>{m.task.subtask}</h2></div>{data.subtasks.map((subtask) => <div className="subtask-row" key={subtask.id}><Circle/><span>{subtask.title}</span><small>{messages.board.priorities[subtask.priority]}</small></div>)}{canWrite ? <form className="mini-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("subtask") as HTMLInputElement; if (input.value.trim()) void api.createSubtask(taskId, { title: input.value.trim(), column_id: data.column_id, priority: "medium" }).then(() => { input.value = ""; invalidate() }) }}><input name="subtask" placeholder={m.task.addSubtask}/><button><Plus/></button></form> : null}</section><section className="task-section"><div className="section-heading"><h2><CheckCircle2/>{m.task.checklist}</h2>{canWrite ? <button className="ghost" onClick={() => { const title = window.prompt(m.task.addChecklist); if (title) void api.createChecklist(taskId, title).then(() => client.invalidateQueries({ queryKey: ["checklists", taskId] })) }}><Plus/>{m.task.addChecklist}</button> : null}</div>{checklists.data?.data.map((list) => <div className="checklist" key={list.id}><div className="checklist-head"><b>{list.title}</b><span>{list.completed_items}/{list.total_items}</span>{canWrite ? <button className="text-danger" onClick={() => void api.deleteChecklist(list.id).then(() => client.invalidateQueries({ queryKey: ["checklists", taskId] }))}>{m.task.remove}</button> : null}</div><progress value={list.completed_items} max={Math.max(1, list.total_items)}/>{list.items.map((item) => <label key={item.id}><input type="checkbox" checked={item.completed} disabled={!canWrite} onChange={() => void api.updateChecklistItem(item.id, { completed: !item.completed }).then(() => client.invalidateQueries({ queryKey: ["checklists", taskId] }))}/><span>{item.title}</span>{canWrite ? <button className="text-danger" onClick={() => void api.deleteChecklistItem(item.id).then(() => client.invalidateQueries({ queryKey: ["checklists", taskId] }))}><X/></button> : null}</label>)}{canWrite ? <form className="mini-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("item") as HTMLInputElement; if (input.value.trim()) void api.addChecklistItem(list.id, input.value.trim()).then(() => { input.value = ""; client.invalidateQueries({ queryKey: ["checklists", taskId] }) }) }}><input name="item" placeholder={m.task.addItem}/><button><Plus/></button></form> : null}</div>)}</section><section className="task-section"><div className="section-heading"><h2><Paperclip/>{m.task.attachment}</h2>{canWrite ? <label className="ghost">{m.task.upload}<input hidden type="file" onChange={(event) => { const file = event.target.files?.[0]; if (file) void api.uploadAttachment(taskId, file).then(() => client.invalidateQueries({ queryKey: ["attachments", taskId] })) }}/></label> : null}</div><div className="attachment-list">{attachments.data?.data.map((file) => <div key={file.id}><a href={api.attachmentUrl(file.id)} target="_blank"><Paperclip/><span>{file.original_name}</span><small>{Math.ceil(file.size_bytes / 1024)} KB</small></a>{canWrite ? <button className="text-danger" onClick={() => void api.deleteAttachment(file.id).then(() => client.invalidateQueries({ queryKey: ["attachments", taskId] }))}>{m.task.remove}</button> : null}</div>)}</div></section>{canWrite ? <button className="danger" onClick={() => void api.archiveTask(taskId, Boolean(data.archived_at)).then(() => { invalidate(); onClose() })}>{data.archived_at ? <RotateCcw/> : <Archive/>}{data.archived_at ? m.task.restore : m.task.archive}</button> : null}</div><aside className="task-activity"><div className="activity-title"><MessageSquare/><h2>{m.task.commentsActivity}</h2></div><form className="comment-composer" onSubmit={(event) => { event.preventDefault(); const input = event.currentTarget.elements.namedItem("comment") as HTMLInputElement; if (input.value.trim()) { addComment.mutate(input.value.trim()); input.value = "" } }}><input name="comment" placeholder={m.task.commentPlaceholder} disabled={!canWrite}/><button disabled={!canWrite}>{m.task.sendComment}</button></form><div className="comment-list">{comments.data?.data.map((comment) => <article key={comment.id}><span className="avatar small">{comment.author_id.slice(0, 2)}</span><div><b>{comment.author_id.slice(0, 8)}</b><p>{comment.body}</p><small>{dateText(comment.created_at)}</small>{canWrite ? <button className="text-danger" onClick={() => void api.deleteComment(comment.id).then(() => client.invalidateQueries({ queryKey: ["comments", taskId] }))}>{m.task.remove}</button> : null}</div></article>)}{!comments.data?.data.length ? <p className="empty-copy">{m.task.noComments}</p> : null}</div><ActivityPanel items={activity.data?.data ?? []}/></aside></Dialog>
}

*/
function ActivityPanel({ items }: { items: Activity[] }) { return <section className="activity-panel"><h2>{m.project.activity}</h2>{items.map((item) => <div key={item.id}><span className="activity-dot"/><p>{item.action}</p><small>{dateText(item.created_at)}</small></div>)}</section> }
function MetricGrid({ values, loading = false }: { values: { label: string; value: number }[]; loading?: boolean }) { return <section className="metric-grid">{loading ? Array.from({ length: 4 }, (_, index) => <div className="metric-card skeleton" key={index}/>) : values.map((item) => <article className="metric-card" key={item.label}><span>{item.label}</span><strong>{new Intl.NumberFormat("fa-IR").format(item.value)}</strong><i/></article>)}</section> }
function ComposerDialog({ type, onClose, mutation }: { type: "workspace" | "project"; onClose: () => void; mutation: { mutate: (form: HTMLFormElement) => void; isPending: boolean; isError: boolean; error: unknown } }) { return <Dialog onClose={onClose}><section className="composer-dialog"><h2>{type === "workspace" ? m.workspace.create : m.workspace.newProject}</h2><form onSubmit={(event) => { event.preventDefault(); mutation.mutate(event.currentTarget) }}><Field name="name" label={type === "workspace" ? m.workspace.name : m.workspace.projectName}/>{type === "project" ? <Field name="key" label={m.workspace.projectKey} dir="ltr"/> : <TextArea name="description" label={m.workspace.description}/>} {mutation.isError ? <ErrorNote error={mutation.error}/> : null}<button className="primary" disabled={mutation.isPending}>{m.create}</button></form></section></Dialog> }
function Dialog({ children, onClose, className = "" }: { children: ReactNode; onClose: () => void; className?: string }) { useEffect(() => { const listener = (event: KeyboardEvent) => { if (event.key === "Escape") onClose() }; window.addEventListener("keydown", listener); return () => window.removeEventListener("keydown", listener) }, [onClose]); return <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) onClose() }}><div className={`dialog ${className}`} role="dialog" aria-modal="true"><button className="dialog-close" aria-label={m.close} onClick={onClose}><X/></button>{children}</div></div> }
function Field(props: { name: string; label: string; type?: string; autoComplete?: string; dir?: string; defaultValue?: string; disabled?: boolean }) { return <label className="field"><span>{props.label}</span><input {...props}/></label> }
function TextArea(props: { name: string; label: string; defaultValue?: string; disabled?: boolean }) { return <label className="field"><span>{props.label}</span><textarea {...props}/></label> }
function ErrorNote({ error }: { error: unknown }) { return <p className="error-note">{errorText(error)}</p> }
function FullLoader() { return <main className="full-loader"><div className="brand-mark"><Columns3/><span>{m.brand}</span></div><LoaderCircle className="spin"/><p>{m.loading}</p></main> }
function InlineLoader() { return <div className="inline-loader"><LoaderCircle className="spin"/><span>{m.loading}</span></div> }
function ErrorState({ error, retry }: { error: unknown; retry: () => void }) { return <div className="error-state"><Circle/><h2>{errorText(error)}</h2><button className="ghost" onClick={retry}>{m.retry}</button></div> }
function EmptyState({ text, action, onAction }: { text: string; action?: string; onAction?: () => void }) { return <div className="empty-state"><Columns3/><h2>{text}</h2>{action ? <button className="primary" onClick={onAction}><Plus/>{action}</button> : null}</div> }
