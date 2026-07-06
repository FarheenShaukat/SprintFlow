"use client";

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { useParams } from "next/navigation";
import { Filter, Maximize2, Minus, Plus } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { RowSkeleton } from "@/components/ui/skeleton";
import { TaskCard } from "@/components/task-card";
import { TaskDetailModal } from "@/components/task-detail-modal";
import { authApi, projectApi, taskApi, type ApiTask, type ProjectMember, type User } from "@/lib/api";
import type { Status, Task } from "@/types/domain";

const columns: { id: Status; title: string }[] = [
  { id: "todo", title: "To Do" },
  { id: "in_progress", title: "In Progress" },
  { id: "review", title: "Review" },
  { id: "done", title: "Done" }
];

function mapTask(task: ApiTask): Task {
  const assigneeName = task.assignee_detail?.full_name ?? "Unassigned";
  return {
    id: task.id,
    key: `SFA-${task.id}`,
    title: task.title,
    description: task.description || "No description yet.",
    status: task.status,
    priority: task.priority,
    assignee: {
      id: task.assignee_detail?.id ?? 0,
      fullName: assigneeName,
      role: "Team member",
      activeTasks: 0,
      capacity: 0
    },
    dueDate: task.due_date ?? "No due date",
    comments: task.comment_count,
    attachments: task.attachment_count,
    isBlocked: task.is_blocked,
    blockedReason: task.blocked_reason,
    aiRiskScore: task.ai_risk_score,
    estimatedHours: Number(task.estimated_hours ?? 0)
  };
}

export default function KanbanPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const [apiTasks, setApiTasks] = useState<ApiTask[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [selected, setSelected] = useState<Task | null>(null);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<ApiTask["priority"]>("medium");
  const [dueDate, setDueDate] = useState("");
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [boardZoom, setBoardZoom] = useState(0.9);

  async function load(query = "") {
    setLoading(true);
    try {
      const result = await taskApi.list(projectId, query);
      setApiTasks(result.results);
      setError("");
    } catch {
      setError("Could not load tasks. Make sure you are signed in and the project exists.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (projectId) {
      void load(filter);
      projectApi.members(projectId).then((result) => setMembers(result.results)).catch(() => setMembers([]));
      authApi.me().then(setCurrentUser).catch(() => setCurrentUser(null));
    }
  }, [projectId, filter]);

  async function createTask() {
    if (!title.trim()) return;
    await taskApi.create(projectId, { title, priority, status: "todo", description: "", due_date: dueDate || null });
    setTitle("");
    setPriority("medium");
    setDueDate("");
    await load(filter);
  }

  async function saveTask(taskId: number, values: Partial<ApiTask>) {
    const updatedTask = await taskApi.update(taskId, values);
    setApiTasks((current) => current.map((item) => item.id === taskId ? updatedTask : item));
    setSelected(mapTask(updatedTask));
  }

  const tasks = useMemo(() => apiTasks.map(mapTask), [apiTasks]);
  const grouped = useMemo(() => columns.map((column) => ({ ...column, tasks: tasks.filter((task) => task.status === column.id) })), [tasks]);
  const canvasBackground = {
    backgroundImage: "radial-gradient(circle at 1px 1px, rgba(53, 37, 205, 0.16) 1px, transparent 0)",
    backgroundSize: "24px 24px"
  };
  const zoomStyle = { zoom: boardZoom } as CSSProperties;

  return (
    <AppShell active="Sprint Planner">
      <div className="flex h-[calc(100vh-4rem)] flex-col overflow-hidden">
        <div className="border-b border-outline-variant bg-surface px-6 py-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <p className="text-sm text-on-surface-variant">Project / Live Kanban</p>
              <h1 className="text-3xl font-bold leading-tight">Project Board</h1>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex flex-wrap gap-2 rounded-xl border border-outline-variant bg-surface-container-low p-1">
                <Button className="h-9 rounded-lg" variant={filter === "" ? "primary" : "ghost"} onClick={() => setFilter("")}><Filter size={16} /> All</Button>
                <Button className="h-9 rounded-lg" variant={filter === "?mine=true" ? "primary" : "ghost"} onClick={() => setFilter("?mine=true")}><Filter size={16} /> My Tasks</Button>
                <Button className="h-9 rounded-lg" variant={filter === "?blocked=true" ? "primary" : "ghost"} onClick={() => setFilter("?blocked=true")}><Filter size={16} /> Blocked</Button>
                <Button className="h-9 rounded-lg" variant={filter === "?priority=high" ? "primary" : "ghost"} onClick={() => setFilter("?priority=high")}><Filter size={16} /> High</Button>
                <Button className="h-9 rounded-lg" variant={filter === "?due=today" ? "primary" : "ghost"} onClick={() => setFilter("?due=today")}><Filter size={16} /> Due today</Button>
              </div>
              <div className="flex items-center gap-1 rounded-xl border border-outline-variant bg-surface-container-low p-1">
                <button className="grid h-9 w-9 place-items-center rounded-lg text-on-surface-variant hover:bg-surface" onClick={() => setBoardZoom((value) => Math.max(0.75, value - 0.05))} aria-label="Zoom out"><Minus size={16} /></button>
                <span className="w-12 text-center text-sm font-semibold">{Math.round(boardZoom * 100)}%</span>
                <button className="grid h-9 w-9 place-items-center rounded-lg text-on-surface-variant hover:bg-surface" onClick={() => setBoardZoom((value) => Math.min(1, value + 0.05))} aria-label="Zoom in"><Plus size={16} /></button>
                <button className="grid h-9 w-9 place-items-center rounded-lg text-on-surface-variant hover:bg-surface" onClick={() => setBoardZoom(0.85)} aria-label="Fit board"><Maximize2 size={16} /></button>
              </div>
            </div>
          </div>
        </div>
        <div className="border-b border-outline-variant bg-surface-container-low px-6 py-4">
          <div className="flex flex-col gap-3 rounded-xl border border-outline-variant bg-surface p-3 shadow-sm md:flex-row">
            <input value={title} onChange={(event) => setTitle(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-outline-variant bg-surface-container-low px-4 py-3 outline-none focus:border-primary" placeholder="Create a task..." />
            <select value={priority} onChange={(event) => setPriority(event.target.value as ApiTask["priority"])} className="rounded-lg border border-outline-variant bg-surface-container-low px-3 py-3 outline-none focus:border-primary">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="rounded-lg border border-outline-variant bg-surface-container-low px-3 py-3 outline-none focus:border-primary" aria-label="Task due date" />
            <Button onClick={createTask} className="px-5"><Plus size={18} /> Add Task</Button>
          </div>
          {error ? <p className="mt-3 text-sm text-error">{error}</p> : null}
        </div>
        <div className="flex-1 overflow-auto bg-[#fbf9ff] p-5" style={canvasBackground}>
          <div className="min-w-[1120px] transition-all duration-200" style={zoomStyle}>
            <div className="grid grid-cols-4 gap-4">
              {grouped.map((column) => (
                <section key={column.id} className="min-w-0 rounded-xl border border-outline-variant bg-surface/85 p-3 shadow-sm backdrop-blur">
                  <div className="mb-3 flex items-center justify-between">
                    <h2 className="font-mono text-sm font-bold uppercase tracking-wider">{column.title}</h2>
                    <span className="grid h-8 w-8 place-items-center rounded-full bg-surface-variant text-xs font-bold">{column.tasks.length}</span>
                  </div>
                  <div className="max-h-[calc(100vh-22rem)] space-y-3 overflow-y-auto pr-1">{loading ? Array.from({ length: 3 }).map((_, index) => <RowSkeleton key={index} />) : column.tasks.map((task) => <TaskCard task={task} key={task.id} onOpen={setSelected} />)}</div>
                </section>
              ))}
            </div>
          </div>
        </div>
      </div>
      <TaskDetailModal task={selected} onClose={() => setSelected(null)} onSave={saveTask} members={members} currentUser={currentUser} />
    </AppShell>
  );
}
