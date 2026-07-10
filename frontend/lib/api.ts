function getApiUrl() {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL;
  if (typeof window === "undefined") return configuredUrl || "/api";

  const isLocalPage = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  if (!configuredUrl) return isLocalPage ? "http://localhost:8000/api" : "/api";

  const pointsToLocalBackend = configuredUrl.includes("localhost") || configuredUrl.includes("127.0.0.1");

  return !isLocalPage && pointsToLocalBackend ? "/api" : configuredUrl;
}

const API_URL = getApiUrl();
const ACCESS_TOKEN_KEY = "sprintflow_access";
const REFRESH_TOKEN_KEY = "sprintflow_refresh";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RefreshResponse = {
  access: string;
  refresh?: string;
};

let refreshPromise: Promise<string | null> | null = null;

function isBrowser() {
  return typeof window !== "undefined";
}

function getAccessToken() {
  return isBrowser() ? localStorage.getItem(ACCESS_TOKEN_KEY) : null;
}

function setTokens(tokens: RefreshResponse) {
  if (!isBrowser()) return;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  if (tokens.refresh) localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

function normalizeApiPath(path: string) {
  const [pathname, query = ""] = path.split("?");
  const normalizedPath = pathname.length > 1 && pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
  return query ? `${normalizedPath}?${query}` : normalizedPath;
}

export function clearAuthTokens() {
  if (!isBrowser()) return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function notifySessionExpired() {
  if (!isBrowser()) return;
  clearAuthTokens();
  window.dispatchEvent(new CustomEvent("sprintflow:session-expired"));
}

async function refreshAccessToken() {
  if (!isBrowser()) return null;
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refresh) return null;

  refreshPromise ??= fetch(`${API_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh })
  })
    .then(async (response) => {
      if (!response.ok) return null;
      const tokens = await response.json() as RefreshResponse;
      setTokens(tokens);
      return tokens.access;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

async function request(path: string, options: RequestInit = {}, accessToken: string | null = getAccessToken()) {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  return fetch(`${API_URL}${normalizeApiPath(path)}`, { ...options, headers });
}

async function parseError(response: Response) {
  let message = `API request failed: ${response.status}`;
  try {
    const data = await response.clone().json();
    if (typeof data === "string") return data;
    if ("detail" in data && typeof data.detail === "string") return data.detail;
    if ("non_field_errors" in data && Array.isArray(data.non_field_errors)) {
      return String(data.non_field_errors[0]);
    }
    const firstValue = Object.values(data)[0];
    message = Array.isArray(firstValue) ? String(firstValue[0]) : JSON.stringify(data);
  } catch {
    try {
      const text = await response.clone().text();
      const title = text.match(/<title>(.*?)<\/title>/is)?.[1];
      if (title) return title.replace(/\s+/g, " ").trim();
      const heading = text.match(/<h1>(.*?)<\/h1>/is)?.[1];
      if (heading) return heading.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
      if (text.includes("DisallowedHost")) {
        return "Backend rejected this production domain. Set DJANGO_ALLOWED_HOSTS correctly on Vercel.";
      }
      if (text.trim()) return text.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 180);
    } catch {
      // Keep the status-based message.
    }
  }
  return message;
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response = await request(path, options);
  const isAuthRequest = path.startsWith("/auth/login") || path.startsWith("/auth/register") || path.startsWith("/auth/refresh");

  if (response.status === 401 && !isAuthRequest) {
    const newAccessToken = await refreshAccessToken();
    if (newAccessToken) {
      response = await request(path, options, newAccessToken);
    } else {
      notifySessionExpired();
    }
  }

  if (!response.ok) {
    if (response.status === 401 && !isAuthRequest) notifySessionExpired();
    throw new ApiError(await parseError(response), response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type User = {
  id: number;
  full_name: string;
  email: string;
  avatar_url: string;
};

export type Workspace = {
  id: number;
  name: string;
  description: string;
  owner: User;
  member_count: number;
  allow_member_create_projects: boolean;
  allow_member_create_tasks: boolean;
  allow_member_edit_tasks: boolean;
  allow_member_comment: boolean;
  allow_member_upload_attachments: boolean;
  allow_member_invite_members: boolean;
};

export type WorkspaceMember = {
  id: number;
  role: "owner" | "admin" | "member";
  user: User;
  joined_at: string;
};

export type WorkspaceInvitation = {
  id: number;
  workspace: number;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "member";
  status: "pending" | "accepted";
  email_sent: boolean;
  email_error: string;
  accepted_at: string | null;
  created_at: string;
};

export type InvitationAccept = {
  email: string;
  full_name: string;
  workspace_id: number;
  workspace_name: string;
  status: "pending" | "accepted";
  user_exists: boolean;
};

export type Project = {
  id: number;
  workspace: number;
  name: string;
  description: string;
  status: "active" | "archived" | "completed";
  start_date: string | null;
  deadline: string | null;
  task_count: number;
  user_project_role: "admin" | "member" | "viewer" | null;
};

export type ApiTask = {
  id: number;
  project: number;
  sprint: number | null;
  title: string;
  description: string;
  status: "todo" | "in_progress" | "review" | "done";
  priority: "low" | "medium" | "high" | "critical";
  assignee: number | null;
  assignee_detail: User | null;
  reporter_detail: User;
  due_date: string | null;
  estimated_hours: string | null;
  actual_hours: string | null;
  is_blocked: boolean;
  blocked_reason: string;
  ai_priority_reason: string;
  ai_risk_score: number;
  comment_count: number;
  attachment_count: number;
};

export type ApiComment = {
  id: number;
  task: number;
  user: User;
  content: string;
  created_at: string;
};

export type ApiSubTask = {
  id: number;
  task: number;
  title: string;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
};

export type ProjectMember = {
  id: number;
  project: number;
  user: User;
  role: "admin" | "member" | "viewer";
  joined_at: string;
};

export type ProjectReport = {
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  blocked_tasks: number;
  completion_rate: number;
  sprint_health_score: number;
  tasks_by_status: { status: string; count: number }[];
  tasks_by_priority: { priority: string; count: number }[];
  workload: { assignee__id: number | null; assignee__full_name: string | null; active_tasks: number }[];
};

export type SprintFlowMessage = {
  id: number;
  role: "user" | "assistant";
  message_type: "text" | "progress" | "plan_card" | "confirmation" | "context_summary";
  content: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type GeneratedPlan = {
  id: number;
  plan_json: SprintFlowPlan;
  validation_errors: string[];
  status: "drafting" | "ready_for_approval" | "applied";
  applied_project: number | null;
  created_at: string;
  updated_at: string;
};

export type SprintFlowPlanTask = {
  title: string;
  description: string;
  sequence: number;
  priority: "low" | "medium" | "high" | "critical";
  estimated_hours: number;
  acceptance_criteria: string[];
  subtasks: string[];
  depends_on: string[];
};

export type SprintFlowPlan = {
  project: {
    name: string;
    description: string;
    goals: string[];
    assumptions: string[];
    risks: string[];
  };
  sprints: {
    name: string;
    goal: string;
    sequence: number;
    start_date: string;
    end_date: string;
    tasks: SprintFlowPlanTask[];
  }[];
};

export type SprintFlowConversation = {
  id: number;
  workspace: number;
  project: number | null;
  thread_id: string;
  status: "active" | "archived";
  agent_status: "idle" | "running" | "awaiting_approval" | "applying" | "completed" | "failed";
  current_step: string;
  last_agent_error: string;
  last_context_synced_at: string | null;
  latest_plan: GeneratedPlan | null;
  messages: SprintFlowMessage[];
  created_at: string;
  updated_at: string;
};

export type SprintFlowEvents = {
  conversation_id: number;
  status: "active" | "archived";
  agent_status: SprintFlowConversation["agent_status"];
  current_step: string;
  last_agent_error: string;
  checkpoint: {
    thread_id: string;
    state: Record<string, unknown>;
  };
  latest_run: {
    id: number;
    status: "running" | "awaiting_approval" | "completed" | "failed";
    current_step: string;
    provider: string;
    error: string;
    metadata: Record<string, unknown>;
    started_at: string;
    completed_at: string | null;
  } | null;
  context_summary: {
    sprints: number;
    tasks: number;
    overdue: number;
    completion_rate: number;
  };
  latest_plan: GeneratedPlan | null;
  pending_approval: boolean;
};

export type SprintFlowApplyResult = {
  project_id: number;
  sprint_count: number;
  task_count: number;
  skipped_existing_sprints: number;
  skipped_existing_tasks: number;
  redirect_url: string;
  already_applied?: boolean;
};

function body(data: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(data) };
}

export const authApi = {
  login: (data: { email: string; password: string }) =>
    api<{ access: string; refresh: string; user: User }>("/auth/login/", body(data)),
  register: (data: { full_name: string; email: string; password: string; avatar_url?: string }) =>
    api<User>("/auth/register/", body(data)),
  me: () => api<User>("/auth/me/")
};

export const workspaceApi = {
  list: () => api<Paginated<Workspace>>("/workspaces/"),
  create: (data: { name: string; description?: string }) => api<Workspace>("/workspaces/", body(data)),
  update: (workspaceId: number, data: Partial<Workspace>) =>
    api<Workspace>(`/workspaces/${workspaceId}/`, { method: "PATCH", body: JSON.stringify(data) }),
  members: (workspaceId: number) => api<Paginated<WorkspaceMember>>(`/workspaces/${workspaceId}/members/`),
  invitations: (workspaceId: number) => api<Paginated<WorkspaceInvitation>>(`/workspaces/${workspaceId}/invitations/`),
  invite: (workspaceId: number, data: { email: string; full_name?: string; role: "admin" | "member" }) =>
    api<WorkspaceInvitation>(`/workspaces/${workspaceId}/invitations/`, body(data))
};

export const invitationApi = {
  preview: (token: string) => api<InvitationAccept>(`/invitations/${token}/accept/`),
  accept: (token: string) => api<InvitationAccept>(`/invitations/${token}/accept/`, { method: "POST" })
};

export const projectApi = {
  list: (workspaceId: number) => api<Paginated<Project>>(`/workspaces/${workspaceId}/projects/`),
  get: (projectId: number) => api<Project>(`/projects/${projectId}/`),
  create: (workspaceId: number, data: { name: string; description?: string; status?: "active" | "archived" | "completed" }) =>
    api<Project>(`/workspaces/${workspaceId}/projects/`, body(data)),
  update: (projectId: number, data: Partial<Project>) =>
    api<Project>(`/projects/${projectId}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (projectId: number) => api<void>(`/projects/${projectId}/`, { method: "DELETE" }),
  members: (projectId: number) => api<Paginated<ProjectMember>>(`/projects/${projectId}/members/`),
  addMember: (projectId: number, data: { user_id: number; role: "admin" | "member" | "viewer" }) =>
    api<ProjectMember>(`/projects/${projectId}/members/`, body(data)),
  updateMember: (projectId: number, membershipId: number, data: { role: "admin" | "member" | "viewer" }) =>
    api<ProjectMember>(`/projects/${projectId}/members/${membershipId}/`, { method: "PATCH", body: JSON.stringify(data) }),
  removeMember: (projectId: number, membershipId: number) =>
    api<void>(`/projects/${projectId}/members/${membershipId}/`, { method: "DELETE" })
};

export const taskApi = {
  list: (projectId: number, query = "") => api<Paginated<ApiTask>>(`/projects/${projectId}/tasks/${query}`),
  create: (projectId: number, data: Partial<ApiTask> & { title: string }) => api<ApiTask>(`/projects/${projectId}/tasks/`, body(data)),
  update: (taskId: number, data: Partial<ApiTask>) =>
    api<ApiTask>(`/tasks/${taskId}/`, { method: "PATCH", body: JSON.stringify(data) })
};

export const commentApi = {
  list: (taskId: number) => api<Paginated<ApiComment>>(`/tasks/${taskId}/comments/`),
  create: (taskId: number, content: string) => api<ApiComment>(`/tasks/${taskId}/comments/`, body({ content }))
};

export const subtaskApi = {
  list: (taskId: number) => api<Paginated<ApiSubTask>>(`/tasks/${taskId}/subtasks/`),
  create: (taskId: number, title: string) => api<ApiSubTask>(`/tasks/${taskId}/subtasks/`, body({ title })),
  update: (taskId: number, subtaskId: number, data: Partial<ApiSubTask>) =>
    api<ApiSubTask>(`/tasks/${taskId}/subtasks/${subtaskId}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (taskId: number, subtaskId: number) =>
    api<void>(`/tasks/${taskId}/subtasks/${subtaskId}/`, { method: "DELETE" })
};

export const reportApi = {
  get: (projectId: number) => api<ProjectReport>(`/projects/${projectId}/reports/`)
};

export const sprintFlowAiApi = {
  getConversation: (projectId: number) => api<SprintFlowConversation>(`/projects/${projectId}/sprintflow-ai/`),
  startNewProjectConversation: (workspaceId: number) => api<SprintFlowConversation>(`/workspaces/${workspaceId}/sprintflow-ai/new/`, { method: "POST" }),
  sendProjectMessage: (projectId: number, data: FormData) =>
    api<SprintFlowMessage[]>(`/projects/${projectId}/sprintflow-ai/messages/`, { method: "POST", body: data }),
  sendNewProjectMessage: (conversationId: number, data: FormData) =>
    api<SprintFlowMessage[]>(`/sprintflow-ai/conversations/${conversationId}/messages/`, { method: "POST", body: data }),
  getProjectEvents: (projectId: number) => api<SprintFlowEvents>(`/projects/${projectId}/sprintflow-ai/events/`),
  approveProjectPlan: (projectId: number, generatedPlanId: number, planJson?: SprintFlowPlan) =>
    api<SprintFlowApplyResult>(`/projects/${projectId}/sprintflow-ai/approve/`, body({ generated_plan_id: generatedPlanId, plan_json: planJson })),
  approveNewProjectPlan: (conversationId: number, generatedPlanId: number, planJson?: SprintFlowPlan) =>
    api<SprintFlowApplyResult>(`/sprintflow-ai/conversations/${conversationId}/approve/`, body({ generated_plan_id: generatedPlanId, plan_json: planJson }))
};
