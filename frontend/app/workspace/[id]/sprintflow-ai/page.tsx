"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Bot, CheckCircle2, FileText, FolderKanban, Loader2, LockKeyhole, Paperclip, Send, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  authApi,
  projectApi,
  sprintFlowAiApi,
  type GeneratedPlan,
  type Project,
  type SprintFlowConversation,
  type SprintFlowMessage,
  type SprintFlowPlan,
  type User,
  type WorkspaceMember,
  workspaceApi
} from "@/lib/api";

type Selection = "new" | number;
type AiProvider = "groq" | "openai";
type ContextSummary = {
  sprints: number;
  tasks: number;
  overdue: number;
  completion_rate: number;
};

export default function SprintFlowAiPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const workspaceId = Number(params.id);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [workspaceMembers, setWorkspaceMembers] = useState<WorkspaceMember[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selection, setSelection] = useState<Selection>("new");
  const [conversation, setConversation] = useState<SprintFlowConversation | null>(null);
  const [messages, setMessages] = useState<SprintFlowMessage[]>([]);
  const [message, setMessage] = useState("");
  const [projectName, setProjectName] = useState("");
  const [aiProvider, setAiProvider] = useState<AiProvider>("groq");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [agentStep, setAgentStep] = useState("");
  const [contextSummary, setContextSummary] = useState<ContextSummary | null>(null);
  const [error, setError] = useState("");
  const [adminOnly, setAdminOnly] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    async function loadProjects() {
      setLoading(true);
      setError("");
      setAdminOnly(false);
      try {
        const [user, workspaceList, memberList] = await Promise.all([
          authApi.me(),
          workspaceApi.list(),
          workspaceApi.members(workspaceId)
        ]);
        setCurrentUser(user);
        setWorkspaceMembers(memberList.results);
        if (!workspaceList.results.some((workspace) => workspace.id === workspaceId)) {
          setError("Workspace not found or you do not have access.");
          return;
        }
        const result = await projectApi.list(workspaceId);
        setProjects(result.results);
        const canStart = memberList.results.some((member) => member.user.id === user.id && ["owner", "admin"].includes(member.role));
        const aiProject = canStart ? result.results[0] : result.results.find((project) => project.user_project_role === "admin");
        if (aiProject) {
          setSelection(aiProject.id);
          await openProjectConversation(aiProject.id);
        } else {
          if (canStart) await startNewConversation();
          else {
            setAdminOnly(true);
            setError("Only admins can access SprintFlow AI.");
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Could not load SprintFlow AI.";
        if (message.toLowerCase().includes("admin")) {
          setAdminOnly(true);
          setError("Only admins can access SprintFlow AI.");
        } else {
          setError(message);
        }
      } finally {
        setLoading(false);
      }
    }

    if (workspaceId) void loadProjects();
  }, [workspaceId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  useEffect(() => {
    const savedDraft = localStorage.getItem("sprintflow_ai_draft");
    if (!savedDraft) return;
    setMessage(savedDraft);
    localStorage.removeItem("sprintflow_ai_draft");
  }, []);

  async function openProjectConversation(projectId: number) {
    setError("");
    const nextConversation = await sprintFlowAiApi.getConversation(projectId);
    const events = await sprintFlowAiApi.getProjectEvents(projectId);
    setConversation(nextConversation);
    setMessages(nextConversation.messages);
    setAgentStep(events.current_step || nextConversation.current_step);
    setContextSummary(events.context_summary);
  }

  async function startNewConversation() {
    setError("");
    const nextConversation = await sprintFlowAiApi.startNewProjectConversation(workspaceId);
    setConversation(nextConversation);
    setMessages(nextConversation.messages);
    setAgentStep(nextConversation.current_step);
    setContextSummary({ sprints: 0, tasks: 0, overdue: 0, completion_rate: 0 });
    setSelection("new");
  }

  async function changeSelection(event: ChangeEvent<HTMLSelectElement>) {
    const value = event.target.value;
    setLoading(true);
    setAdminOnly(false);
    try {
      if (value === "new") {
        await startNewConversation();
      } else {
        const projectId = Number(value);
        setSelection(projectId);
        await openProjectConversation(projectId);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not switch project context.";
      if (message.toLowerCase().includes("admin")) {
        setAdminOnly(true);
        setError("Only admins can access SprintFlow AI.");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!conversation) {
      setError("SprintAI chat is still loading. Choose a project or start a new project first.");
      return;
    }
    if (!message.trim() && !file) return;
    const form = new FormData();
    form.append("content", message);
    form.append("ai_provider", aiProvider);
    if (projectName.trim()) form.append("project_name", projectName);
    if (file) form.append("file", file);
    const userMessage: SprintFlowMessage = {
      id: Date.now(),
      role: "user",
      message_type: "text",
      content: message || `Uploaded ${file?.name}`,
      payload: {},
      created_at: new Date().toISOString()
    };
    setMessages((items) => [...items, userMessage]);
    setSending(true);
    setError("");
    try {
      const nextMessages = conversation.project
        ? await sprintFlowAiApi.sendProjectMessage(conversation.project, form)
        : await sprintFlowAiApi.sendNewProjectMessage(conversation.id, form);
      setMessages((items) => [...items, ...nextMessages]);
      if (conversation.project) {
        const events = await sprintFlowAiApi.getProjectEvents(conversation.project);
        setAgentStep(events.current_step);
        setContextSummary(events.context_summary);
      }
      setMessage("");
      setProjectName("");
      setFile(null);
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not send message.");
    } finally {
      setSending(false);
    }
  }

  async function approvePlan(plan: GeneratedPlan) {
    if (!conversation) return;
    setApprovingId(plan.id);
    setError("");
    try {
      const result = conversation.project
        ? await sprintFlowAiApi.approveProjectPlan(conversation.project, plan.id)
        : await sprintFlowAiApi.approveNewProjectPlan(conversation.id, plan.id);
      if (!conversation.project) {
        const projectResult = await projectApi.list(workspaceId);
        setProjects(projectResult.results);
        setSelection(result.project_id);
        setContextSummary(null);
      }
      setMessages((items) => [
        ...items,
        {
          id: Date.now(),
          role: "assistant",
          message_type: "confirmation",
          content: `Created ${result.sprint_count} sprints and ${result.task_count} tasks.`,
          payload: result,
          created_at: new Date().toISOString()
        }
      ]);
      router.push(result.redirect_url);
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not apply plan.");
    } finally {
      setApprovingId(null);
    }
  }

  const selectedProjectName = useMemo(() => {
    if (selection === "new") return "+ New Project";
    return projects.find((project) => project.id === selection)?.name ?? "Project";
  }, [projects, selection]);
  const workspaceRole = workspaceMembers.find((member) => member.user.id === currentUser?.id)?.role;
  const canStartNewProject = workspaceRole === "owner" || workspaceRole === "admin";
  const aiProjects = projects.filter((project) => canStartNewProject || project.user_project_role === "admin");

  function queuePlanInstruction(instruction: string) {
    setMessage(instruction);
    requestAnimationFrame(() => {
      document.getElementById("sprintflow-composer")?.focus();
    });
  }

  return (
    <AppShell active="Projects">
      <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-7xl flex-col p-4 md:p-6">
        <div className="mb-4 flex flex-col justify-between gap-3 border-b border-outline-variant pb-4 lg:flex-row lg:items-center">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-white">
              <Bot size={22} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">SprintFlow AI</h1>
              <p className="text-sm text-on-surface-variant">Persistent project chat with approval-gated planning.</p>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <select value={selection} onChange={changeSelection} className="rounded-lg border border-outline-variant bg-surface px-3 py-2 text-sm outline-none focus:border-primary">
              {canStartNewProject ? <option value="new">+ New Project</option> : null}
              {aiProjects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
            </select>
            {selection !== "new" ? <Link href={`/projects/${selection}/board`}><Button variant="secondary"><FolderKanban size={16} /> Board</Button></Link> : null}
          </div>
        </div>

        {adminOnly ? (
          <div className="mb-4 rounded-xl border border-outline-variant bg-surface p-6 text-center">
            <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-lg bg-error-container text-error">
              <LockKeyhole size={22} />
            </div>
            <h2 className="text-xl font-semibold">Only admins can access SprintFlow AI</h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-on-surface-variant">Ask a workspace admin to promote you or assign you as a project admin if you need AI planning access.</p>
            <Link href={`/workspace/${workspaceId}`} className="mt-4 inline-flex">
              <Button variant="secondary">Back to workspace</Button>
            </Link>
          </div>
        ) : error ? <div className="mb-4 rounded-xl border border-error/20 bg-error-container p-4 text-sm text-error">{error}</div> : null}

        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm text-on-surface-variant">
          <Badge>{selectedProjectName}</Badge>
          {agentStep ? <Badge tone="low">{agentStep.replaceAll("_", " ")}</Badge> : null}
          {contextSummary ? (
            <>
              <span>{contextSummary.sprints} sprints</span>
              <span>{contextSummary.tasks} tasks</span>
              <span>{contextSummary.overdue} overdue</span>
              <span>{contextSummary.completion_rate}% complete</span>
            </>
          ) : null}
          <span>Live context refreshes on switch and each turn.</span>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto rounded-2xl border border-outline-variant bg-surface p-4">
          {loading ? (
            <div className="grid min-h-80 place-items-center text-on-surface-variant"><Loader2 className="animate-spin" /> Loading chat...</div>
          ) : (
            <div className="space-y-4">
              {messages.map((item) => <MessageBubble key={`${item.id}-${item.created_at}`} message={item} onApprove={approvePlan} onPlanInstruction={queuePlanInstruction} approvingId={approvingId} />)}
              {sending ? <div className="flex items-center gap-2 text-sm text-on-surface-variant"><Loader2 className="animate-spin" size={16} /> Drafting plan...</div> : null}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <form onSubmit={sendMessage} className="mt-4 rounded-2xl border border-outline-variant bg-surface p-3">
          {selection === "new" && canStartNewProject ? (
            <input value={projectName} onChange={(event) => setProjectName(event.target.value)} className="mb-3 w-full rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Optional project name. If empty, SprintFlow AI will derive one." />
          ) : null}
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <textarea id="sprintflow-composer" value={message} onChange={(event) => setMessage(event.target.value)} className="min-h-24 flex-1 rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Ask SprintFlow AI to plan, refine, add tasks, or inspect the current project..." />
            <div className="flex gap-2">
              <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm font-medium hover:bg-surface-container-low">
                <Paperclip size={16} />
                <span>{file ? file.name.slice(0, 18) : "Attach"}</span>
                <input type="file" accept=".pdf,.docx,.txt,.md" className="hidden" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              </label>
              <Button type="submit" disabled={loading || sending || !conversation || (!message.trim() && !file)}>
                {sending ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                Send
              </Button>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <label htmlFor="sprintflow-provider" className="font-medium text-on-surface-variant">Model</label>
            <select
              id="sprintflow-provider"
              value={aiProvider}
              onChange={(event) => setAiProvider(event.target.value as AiProvider)}
              className="rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm outline-none focus:border-primary"
            >
              <option value="groq">Groq</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>
        </form>
      </div>
    </AppShell>
  );
}

function MessageBubble({ message, onApprove, onPlanInstruction, approvingId }: { message: SprintFlowMessage; onApprove: (plan: GeneratedPlan) => void; onPlanInstruction: (instruction: string) => void; approvingId: number | null }) {
  const isUser = message.role === "user";
  if (message.message_type === "plan_card") {
    const payload = message.payload as { generated_plan_id?: number; plan?: SprintFlowPlan; validation_errors?: string[] };
    const plan: GeneratedPlan = {
      id: Number(payload.generated_plan_id),
      plan_json: payload.plan as SprintFlowPlan,
      validation_errors: payload.validation_errors ?? [],
      status: "ready_for_approval",
      applied_project: null,
      created_at: message.created_at,
      updated_at: message.created_at
    };
    return <PlanCard plan={plan} provider={String(message.payload.provider || "fallback")} onApprove={onApprove} onPlanInstruction={onPlanInstruction} approving={approvingId === plan.id} />;
  }
  if (message.message_type === "context_summary") {
    const summary = message.payload as { sprints?: number; tasks?: number; overdue?: number; completion_rate?: number };
    return (
      <div className="rounded-xl border border-outline-variant bg-surface-container-low p-4">
        <div className="mb-2 flex items-center gap-2 font-semibold"><Sparkles size={16} /> Live Context</div>
        <div className="grid gap-3 text-sm sm:grid-cols-4">
          <span>{summary.sprints ?? 0} sprints</span>
          <span>{summary.tasks ?? 0} tasks</span>
          <span>{summary.overdue ?? 0} overdue</span>
          <span>{summary.completion_rate ?? 0}% complete</span>
        </div>
      </div>
    );
  }
  if (message.message_type === "confirmation") {
    const payload = message.payload as { redirect_url?: string };
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800">
        <div className="flex items-center gap-2 font-semibold"><CheckCircle2 size={18} /> {message.content}</div>
        {payload.redirect_url ? <Link className="mt-2 inline-block text-sm font-semibold underline" href={payload.redirect_url}>Open board</Link> : null}
      </div>
    );
  }
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[760px] rounded-2xl px-4 py-3 text-sm ${isUser ? "bg-primary text-white" : "bg-surface-container-low text-on-surface"}`}>
        {message.message_type === "progress" ? <span className="mr-2 inline-flex align-middle"><Loader2 className="animate-spin" size={14} /></span> : null}
        {message.content}
      </div>
    </div>
  );
}

function PlanCard({ plan, provider, onApprove, onPlanInstruction, approving }: { plan: GeneratedPlan; provider: string; onApprove: (plan: GeneratedPlan) => void; onPlanInstruction: (instruction: string) => void; approving: boolean }) {
  const data = plan.plan_json;
  return (
    <div className="rounded-2xl border border-outline-variant bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-primary"><FileText size={16} /> Plan Card <Badge tone="low">{provider}</Badge></div>
          <h2 className="mt-1 text-xl font-bold">{data.project.name}</h2>
          <p className="mt-1 text-sm text-on-surface-variant">{data.project.description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => onPlanInstruction(`Regenerate this plan for ${data.project.name}. Keep the project context, but improve sequencing, dependencies, estimates, and acceptance criteria.`)}>
            Regenerate
          </Button>
          <Button variant="secondary" onClick={() => onPlanInstruction(`Edit this plan: `)}>
            Edit
          </Button>
          <Button onClick={() => onApprove(plan)} disabled={approving || Boolean(plan.validation_errors.length)}>
            {approving ? <Loader2 className="animate-spin" size={16} /> : <CheckCircle2 size={16} />}
            Approve
          </Button>
        </div>
      </div>
      {plan.validation_errors.length ? <div className="mb-4 rounded-lg bg-error-container p-3 text-sm text-error">{plan.validation_errors.join(" ")}</div> : null}
      <div className="space-y-4">
        {data.sprints.map((sprint) => (
          <div key={sprint.name} className="rounded-xl border border-outline-variant p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-semibold">{sprint.name}</h3>
              <Badge tone="low">{sprint.tasks.length} tasks</Badge>
            </div>
            <p className="mt-1 text-sm text-on-surface-variant">{sprint.goal}</p>
            <div className="mt-3 space-y-2">
              {sprint.tasks.map((task) => (
                <div key={task.title} className="rounded-lg bg-surface-container-low p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <strong>{task.title}</strong>
                    <Badge tone={task.priority}>{task.priority}</Badge>
                  </div>
                  <p className="mt-1 text-on-surface-variant">{task.description}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
