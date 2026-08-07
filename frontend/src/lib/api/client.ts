import type { components } from "./schema"

type S = components["schemas"]

export type User = S["UserPublic"]
export type Workspace = S["WorkspacePublic"]
export type WorkspaceMember = S["MemberPublic"]
export type Invitation = S["InvitationPublic"]
export type Project = S["ProjectPublic"]
export type ProjectMember = S["ProjectMemberPublic"]
export type Column = S["ColumnPublic"]
export type Task = S["TaskPublic"]
export type TaskDetail = S["TaskDetailPublic"]
export type Label = S["LabelPublic"]
export type Comment = S["CommentPublic"]
export type Checklist = S["ChecklistDetailPublic"]
export type ChecklistItem = S["ChecklistItemPublic"]
export type Attachment = S["AttachmentPublic"]
export type Activity = S["ActivityPublic"]
export type Notification = S["NotificationPublic"]
export type GlobalMetrics = S["GlobalDashboard"]
export type ProjectMetrics = S["ProjectMetrics"]

const apiBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
let accessToken: string | null = null
let refreshFlight: Promise<string | null> | null = null

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "request_failed",
  ) {
    super(message)
  }
}

type RequestOptions = RequestInit & { auth?: boolean; retry?: boolean }

function parseError(payload: unknown, status: number) {
  if (payload && typeof payload === "object") {
    const body = payload as { error?: { code?: string; message?: string }; detail?: string }
    return new ApiError(body.error?.message ?? body.detail ?? "درخواست انجام نشد.", status, body.error?.code)
  }
  return new ApiError("درخواست انجام نشد.", status)
}

async function rawRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (typeof options.body === "string" && !headers.has("Content-Type")) headers.set("Content-Type", "application/json")
  if (options.auth !== false && accessToken) headers.set("Authorization", `Bearer ${accessToken}`)
  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers, credentials: "include" })
  if (response.status === 401 && options.auth !== false && options.retry !== false) {
    const refreshed = await refreshAccessToken()
    if (refreshed) return rawRequest<T>(path, { ...options, retry: false })
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw parseError(payload, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

async function rawBlob(path: string, options: RequestOptions = {}): Promise<Blob> {
  const headers = new Headers(options.headers)
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`)
  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers, credentials: "include" })
  if (response.status === 401 && options.retry !== false && await refreshAccessToken()) {
    return rawBlob(path, { ...options, retry: false })
  }
  if (!response.ok) throw parseError(await response.json().catch(() => null), response.status)
  return response.blob()
}

export async function refreshAccessToken() {
  if (!refreshFlight) {
    refreshFlight = rawRequest<S["TokenResponse"]>("/api/v1/auth/refresh", { method: "POST", auth: false, retry: false })
      .then((result) => (accessToken = result.access_token))
      .catch(() => (accessToken = null))
      .finally(() => { refreshFlight = null })
  }
  return refreshFlight
}

const json = (value: unknown) => JSON.stringify(value)
const page = "?page=1&page_size=100"

export const api = {
  request: rawRequest,
  register: (payload: S["UserRegistration"]) => rawRequest<S["UserResponse"]>("/api/v1/auth/register", { method: "POST", body: json(payload), auth: false }),
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password })
    const result = await rawRequest<S["TokenResponse"]>("/api/v1/auth/token", { method: "POST", body, auth: false })
    accessToken = result.access_token
    return result
  },
  logout: async () => { await rawRequest<void>("/api/v1/auth/logout", { method: "POST", auth: false }); accessToken = null },
  me: () => rawRequest<S["UserResponse"]>("/api/v1/auth/me"),
  updateProfile: (payload: S["ProfileUpdate"]) => rawRequest<S["UserResponse"]>("/api/v1/auth/profile", { method: "PATCH", body: json(payload) }),
  uploadAvatar: (file: File) => { const body = new FormData(); body.set("file", file); return rawRequest<S["UserResponse"]>("/api/v1/auth/profile/avatar", { method: "POST", body }) },
  deleteAvatar: () => rawRequest<void>("/api/v1/auth/profile/avatar", { method: "DELETE" }),

  workspaces: (includeArchived = false) => rawRequest<S["WorkspaceListResponse"]>(`/api/v1/workspaces${page}&include_archived=${includeArchived}`),
  workspace: (id: string) => rawRequest<S["WorkspaceResponse"]>(`/api/v1/workspaces/${id}`),
  createWorkspace: (payload: S["WorkspaceCreate"]) => rawRequest<S["WorkspaceResponse"]>("/api/v1/workspaces", { method: "POST", body: json(payload) }),
  updateWorkspace: (id: string, payload: S["WorkspaceUpdate"]) => rawRequest<S["WorkspaceResponse"]>(`/api/v1/workspaces/${id}`, { method: "PATCH", body: json(payload) }),
  archiveWorkspace: (id: string, restore = false) => rawRequest<S["WorkspaceResponse"]>(`/api/v1/workspaces/${id}/${restore ? "restore" : "archive"}`, { method: "POST" }),
  deleteWorkspace: (id: string) => rawRequest<void>(`/api/v1/workspaces/${id}`, { method: "DELETE" }),
  workspaceMembers: (id: string) => rawRequest<S["MemberListResponse"]>(`/api/v1/workspaces/${id}/members${page}`),
  addWorkspaceMember: (id: string, payload: S["MemberCreate"]) => rawRequest<S["MemberResponse"]>(`/api/v1/workspaces/${id}/members`, { method: "POST", body: json(payload) }),
  updateWorkspaceMember: (workspaceId: string, memberId: string, payload: S["MemberRoleUpdate"]) => rawRequest<S["MemberResponse"]>(`/api/v1/workspaces/${workspaceId}/members/${memberId}`, { method: "PATCH", body: json(payload) }),
  removeWorkspaceMember: (workspaceId: string, memberId: string) => rawRequest<void>(`/api/v1/workspaces/${workspaceId}/members/${memberId}`, { method: "DELETE" }),
  invitations: (id: string) => rawRequest<S["InvitationListResponse"]>(`/api/v1/workspaces/${id}/invitations${page}`),
  invite: (id: string, payload: S["InvitationCreate"]) => rawRequest<S["InvitationCreatedResponse"]>(`/api/v1/workspaces/${id}/invitations`, { method: "POST", body: json(payload) }),
  revokeInvitation: (workspaceId: string, id: string) => rawRequest<S["InvitationResponse"]>(`/api/v1/workspaces/${workspaceId}/invitations/${id}/revoke`, { method: "POST" }),
  acceptInvitation: (token: string) => rawRequest<S["MemberResponse"]>(`/api/v1/invitations/${token}/accept`, { method: "POST" }),

  projects: (workspaceId: string, includeArchived = false) => rawRequest<S["ProjectListResponse"]>(`/api/v1/workspaces/${workspaceId}/projects${page}&include_archived=${includeArchived}`),
  project: (id: string) => rawRequest<S["ProjectResponse"]>(`/api/v1/projects/${id}`),
  createProject: (workspaceId: string, payload: S["ProjectCreate"]) => rawRequest<S["ProjectResponse"]>(`/api/v1/workspaces/${workspaceId}/projects`, { method: "POST", body: json(payload) }),
  updateProject: (id: string, payload: S["ProjectUpdate"]) => rawRequest<S["ProjectResponse"]>(`/api/v1/projects/${id}`, { method: "PATCH", body: json(payload) }),
  archiveProject: (id: string, restore = false) => rawRequest<S["ProjectResponse"]>(`/api/v1/projects/${id}/${restore ? "restore" : "archive"}`, { method: "POST" }),
  projectMembers: (id: string) => rawRequest<S["ProjectMemberListResponse"]>(`/api/v1/projects/${id}/members${page}`),
  addProjectMember: (id: string, payload: S["ProjectMemberCreate"]) => rawRequest<S["ProjectMemberResponse"]>(`/api/v1/projects/${id}/members`, { method: "POST", body: json(payload) }),
  updateProjectMember: (projectId: string, memberId: string, payload: S["ProjectMemberRoleUpdate"]) => rawRequest<S["ProjectMemberResponse"]>(`/api/v1/projects/${projectId}/members/${memberId}`, { method: "PATCH", body: json(payload) }),
  removeProjectMember: (projectId: string, memberId: string) => rawRequest<void>(`/api/v1/projects/${projectId}/members/${memberId}`, { method: "DELETE" }),
  columns: (projectId: string) => rawRequest<S["ColumnListResponse"]>(`/api/v1/projects/${projectId}/columns${page}`),
  createColumn: (projectId: string, payload: S["ColumnCreate"]) => rawRequest<S["ColumnResponse"]>(`/api/v1/projects/${projectId}/columns`, { method: "POST", body: json(payload) }),
  updateColumn: (projectId: string, columnId: string, payload: S["ColumnUpdate"]) => rawRequest<S["ColumnResponse"]>(`/api/v1/projects/${projectId}/columns/${columnId}`, { method: "PATCH", body: json(payload) }),
  archiveColumn: (projectId: string, columnId: string) => rawRequest<S["ColumnResponse"]>(`/api/v1/projects/${projectId}/columns/${columnId}/archive`, { method: "POST" }),
  reorderColumns: (projectId: string, payload: S["ColumnReorder"]) => rawRequest<S["ColumnListResponse"]>(`/api/v1/projects/${projectId}/columns/reorder`, { method: "PUT", body: json(payload) }),

  tasks: (projectId: string, query = "", includeArchived = false) => rawRequest<S["TaskListResponse"]>(`/api/v1/projects/${projectId}/tasks?page=1&page_size=100&sort=position&include_archived=${includeArchived}${query}`),
  task: (id: string) => rawRequest<S["TaskDetailResponse"]>(`/api/v1/tasks/${id}`),
  createTask: (projectId: string, payload: S["TaskCreate"]) => rawRequest<S["TaskResponse"]>(`/api/v1/projects/${projectId}/tasks`, { method: "POST", body: json(payload) }),
  createSubtask: (taskId: string, payload: S["TaskCreate"]) => rawRequest<S["TaskResponse"]>(`/api/v1/tasks/${taskId}/subtasks`, { method: "POST", body: json(payload) }),
  updateTask: (id: string, payload: S["TaskUpdate"]) => rawRequest<S["TaskResponse"]>(`/api/v1/tasks/${id}`, { method: "PATCH", body: json(payload) }),
  moveTask: (id: string, payload: S["TaskMove"]) => rawRequest<S["TaskResponse"]>(`/api/v1/tasks/${id}/move`, { method: "POST", body: json(payload) }),
  archiveTask: (id: string, restore = false) => rawRequest<S["TaskResponse"]>(`/api/v1/tasks/${id}/${restore ? "restore" : "archive"}`, { method: "POST" }),
  labels: (projectId: string) => rawRequest<S["LabelListResponse"]>(`/api/v1/projects/${projectId}/labels${page}`),
  createLabel: (projectId: string, payload: S["LabelCreate"]) => rawRequest<S["LabelResponse"]>(`/api/v1/projects/${projectId}/labels`, { method: "POST", body: json(payload) }),
  updateLabel: (id: string, payload: S["LabelUpdate"]) => rawRequest<S["LabelResponse"]>(`/api/v1/labels/${id}`, { method: "PATCH", body: json(payload) }),
  archiveLabel: (id: string) => rawRequest<S["LabelResponse"]>(`/api/v1/labels/${id}`, { method: "DELETE" }),
  addAssignee: (taskId: string, userId: string) => rawRequest<void>(`/api/v1/tasks/${taskId}/assignees`, { method: "POST", body: json({ user_id: userId }) }),
  removeAssignee: (taskId: string, userId: string) => rawRequest<void>(`/api/v1/tasks/${taskId}/assignees/${userId}`, { method: "DELETE" }),
  addTaskLabel: (taskId: string, labelId: string) => rawRequest<void>(`/api/v1/tasks/${taskId}/labels`, { method: "POST", body: json({ label_id: labelId }) }),
  removeTaskLabel: (taskId: string, labelId: string) => rawRequest<void>(`/api/v1/tasks/${taskId}/labels/${labelId}`, { method: "DELETE" }),

  comments: (taskId: string) => rawRequest<S["CommentListResponse"]>(`/api/v1/tasks/${taskId}/comments${page}`),
  createComment: (taskId: string, body: string) => rawRequest<S["CommentResponse"]>(`/api/v1/tasks/${taskId}/comments`, { method: "POST", body: json({ body }) }),
  updateComment: (id: string, body: string) => rawRequest<S["CommentResponse"]>(`/api/v1/comments/${id}`, { method: "PATCH", body: json({ body }) }),
  deleteComment: (id: string) => rawRequest<void>(`/api/v1/comments/${id}`, { method: "DELETE" }),
  checklists: (taskId: string) => rawRequest<S["ChecklistListResponse"]>(`/api/v1/tasks/${taskId}/checklists`),
  createChecklist: (taskId: string, title: string) => rawRequest<S["ChecklistResponse"]>(`/api/v1/tasks/${taskId}/checklists`, { method: "POST", body: json({ title }) }),
  updateChecklist: (id: string, title: string) => rawRequest<S["ChecklistResponse"]>(`/api/v1/checklists/${id}`, { method: "PATCH", body: json({ title }) }),
  deleteChecklist: (id: string) => rawRequest<void>(`/api/v1/checklists/${id}`, { method: "DELETE" }),
  addChecklistItem: (id: string, title: string) => rawRequest<S["ChecklistItemResponse"]>(`/api/v1/checklists/${id}/items`, { method: "POST", body: json({ title, completed: false }) }),
  updateChecklistItem: (id: string, payload: S["ChecklistItemUpdate"]) => rawRequest<S["ChecklistItemResponse"]>(`/api/v1/checklist-items/${id}`, { method: "PATCH", body: json(payload) }),
  deleteChecklistItem: (id: string) => rawRequest<void>(`/api/v1/checklist-items/${id}`, { method: "DELETE" }),
  reorderChecklistItems: (id: string, itemIds: string[]) => rawRequest<S["ChecklistItemPublic"][]>(`/api/v1/checklists/${id}/items/reorder`, { method: "PUT", body: json({ item_ids: itemIds }) }),
  attachments: (taskId: string) => rawRequest<S["AttachmentListResponse"]>(`/api/v1/tasks/${taskId}/attachments`),
  uploadAttachment: (taskId: string, file: File) => { const body = new FormData(); body.set("file", file); return rawRequest<S["AttachmentResponse"]>(`/api/v1/tasks/${taskId}/attachments`, { method: "POST", body }) },
  deleteAttachment: (id: string) => rawRequest<void>(`/api/v1/attachments/${id}`, { method: "DELETE" }),
  downloadAttachment: (id: string) => rawBlob(`/api/v1/attachments/${id}/download`),
  avatar: () => rawBlob("/api/v1/auth/profile/avatar"),
  activity: (taskId: string) => rawRequest<S["ActivityListResponse"]>(`/api/v1/tasks/${taskId}/activity`),

  globalDashboard: () => rawRequest<S["GlobalDashboardResponse"]>("/api/v1/dashboard"),
  projectDashboard: (projectId: string) => rawRequest<S["ProjectDashboardResponse"]>(`/api/v1/projects/${projectId}/dashboard`),
  timeline: (projectId: string, start: string, end: string) => rawRequest<S["ReportingTaskListResponse"]>(`/api/v1/projects/${projectId}/timeline?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&page=1&page_size=100`),
  calendar: (projectId: string, start: string, end: string) => rawRequest<S["ReportingTaskListResponse"]>(`/api/v1/projects/${projectId}/calendar?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&page=1&page_size=100`),
  projectActivity: (projectId: string) => rawRequest<S["ProjectActivityResponse"]>(`/api/v1/projects/${projectId}/activity`),
  notifications: () => rawRequest<S["NotificationListResponse"]>("/api/v1/notifications"),
  unreadCount: () => rawRequest<S["NotificationCountResponse"]>("/api/v1/notifications/unread-count"),
  markNotification: (id: string) => rawRequest<void>(`/api/v1/notifications/${id}/read`, { method: "POST" }),
  markAllNotifications: () => rawRequest<void>("/api/v1/notifications/read-all", { method: "POST" }),
}

export const startDemoSession = () => api.login("demo@example.com", "demo-password-change-me")

export async function getBoard() {
  const workspace = (await api.workspaces()).data[0]
  if (!workspace) throw new ApiError("فضای کاری پیدا نشد.", 404, "resource_not_found")
  let project = (await api.projects(workspace.id)).data[0]
  if (!project) project = (await api.createProject(workspace.id, { name: "برنامه‌ریزی محصول", key: "PLAN", is_private: false })).data
  const [columns, tasks] = await Promise.all([api.columns(project.id), api.tasks(project.id)])
  return { workspace, project, columns: columns.data, tasks: tasks.data }
}

export const createTask = (projectId: string, columnId: string, title: string) => api.createTask(projectId, { title, column_id: columnId, priority: "medium" })
export const moveTask = (task: Task, targetColumnId: string, targetIndex: number) => api.moveTask(task.id, { target_column_id: targetColumnId, target_index: targetIndex, version: task.version })
