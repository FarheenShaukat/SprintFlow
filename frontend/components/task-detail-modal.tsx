"use client";

import { useEffect, useState } from "react";
import { X, Bot, Calendar, Loader2, Send, Save } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { commentApi, subtaskApi, type ApiComment, type ApiSubTask, type ApiTask, type ProjectMember, type User } from "@/lib/api";
import type { Task } from "@/types/domain";

type TaskPatch = Partial<Pick<ApiTask, "title" | "description" | "status" | "priority" | "due_date" | "is_blocked" | "blocked_reason" | "assignee">>;

export function TaskDetailModal({
  task,
  onClose,
  onSave,
  members = [],
  currentUser = null
}: {
  task: Task | null;
  onClose: () => void;
  onSave?: (taskId: number, values: TaskPatch) => Promise<void>;
  members?: ProjectMember[];
  currentUser?: User | null;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ApiTask["status"]>("todo");
  const [priority, setPriority] = useState<ApiTask["priority"]>("medium");
  const [dueDate, setDueDate] = useState("");
  const [isBlocked, setIsBlocked] = useState(false);
  const [blockedReason, setBlockedReason] = useState("");
  const [assignee, setAssignee] = useState<number | "">("");
  const [comments, setComments] = useState<ApiComment[]>([]);
  const [subtasks, setSubtasks] = useState<ApiSubTask[]>([]);
  const [subtaskTitle, setSubtaskTitle] = useState("");
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [commentSaving, setCommentSaving] = useState(false);
  const [subtaskSaving, setSubtaskSaving] = useState(false);

  useEffect(() => {
    if (!task) return;
    setTitle(task.title);
    setDescription(task.description === "No description yet." ? "" : task.description);
    setStatus(task.status);
    setPriority(task.priority);
    setDueDate(task.dueDate === "No due date" ? "" : task.dueDate);
    setIsBlocked(Boolean(task.isBlocked));
    setBlockedReason(task.blockedReason ?? "");
    setAssignee(task.assignee.id || "");
    commentApi.list(task.id).then((result) => setComments(result.results)).catch(() => setComments([]));
    subtaskApi.list(task.id).then((result) => setSubtasks(result.results)).catch(() => setSubtasks([]));
  }, [task]);

  if (!task) return null;
  const currentTask = task;

  async function save() {
    setSaving(true);
    setMessage("");
    try {
      await onSave?.(currentTask.id, {
        title,
        description,
        status,
        priority,
        due_date: dueDate || null,
        is_blocked: isBlocked,
        blocked_reason: blockedReason,
        assignee: assignee === "" ? null : Number(assignee)
      });
      setMessage("Task saved.");
    } finally {
      setSaving(false);
    }
  }

  async function addComment() {
    if (!comment.trim()) return;
    setCommentSaving(true);
    try {
      const created = await commentApi.create(currentTask.id, comment);
      setComments((current) => [created, ...current]);
      setComment("");
    } finally {
      setCommentSaving(false);
    }
  }

  async function addSubtask() {
    if (!subtaskTitle.trim()) return;
    setSubtaskSaving(true);
    try {
      const created = await subtaskApi.create(currentTask.id, subtaskTitle);
      setSubtasks((current) => [...current, created]);
      setSubtaskTitle("");
    } finally {
      setSubtaskSaving(false);
    }
  }

  async function toggleSubtask(subtask: ApiSubTask) {
    const updated = await subtaskApi.update(currentTask.id, subtask.id, { is_completed: !subtask.is_completed });
    setSubtasks((current) => current.map((item) => item.id === updated.id ? updated : item));
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/35 p-3 backdrop-blur-sm md:p-6">
      <section className="grid h-[92vh] w-full max-w-6xl overflow-hidden rounded-2xl bg-surface shadow-2xl md:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-h-0 overflow-y-auto p-6 md:p-8">
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge>{task.key}</Badge>
              <Badge tone={priority === "critical" ? "critical" : priority}>{priority}</Badge>
            </div>
            <Button variant="ghost" onClick={onClose} aria-label="Close task detail"><X size={20} /></Button>
          </div>

          <label className="font-mono text-xs font-bold uppercase tracking-wider text-on-surface-variant">Title</label>
          <input value={title} onChange={(event) => setTitle(event.target.value)} className="mt-2 w-full rounded-xl border border-outline-variant px-4 py-3 text-2xl font-bold outline-none focus:border-primary" />

          <div className="mt-8">
            <h3 className="mb-3 font-mono text-xs font-bold uppercase tracking-wider text-on-surface-variant">Description</h3>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} className="min-h-36 w-full rounded-xl border border-outline-variant bg-surface-container-low p-5 leading-7 outline-none focus:border-primary" placeholder="Add task description..." />
          </div>

          <div className="mt-8 border-t border-outline-variant pt-8">
            <h3 className="mb-3 font-mono text-xs font-bold uppercase tracking-wider text-on-surface-variant">Subtasks</h3>
            <div className="flex gap-3">
              <input value={subtaskTitle} onChange={(event) => setSubtaskTitle(event.target.value)} className="flex-1 rounded-xl border border-outline-variant bg-surface-container-low px-4 py-3 outline-none focus:border-primary" placeholder="Add a subtask..." />
              <Button onClick={addSubtask} disabled={subtaskSaving}>{subtaskSaving ? <Loader2 className="animate-spin" size={16} /> : null} Add</Button>
            </div>
            <div className="mt-4 space-y-2">
              {subtasks.map((subtask) => (
                <label key={subtask.id} className="flex items-center gap-3 rounded-lg border border-outline-variant p-3 text-sm">
                  <input type="checkbox" checked={subtask.is_completed} onChange={() => void toggleSubtask(subtask)} />
                  <span className={subtask.is_completed ? "line-through text-on-surface-variant" : ""}>{subtask.title}</span>
                </label>
              ))}
              {!subtasks.length ? <p className="text-sm text-on-surface-variant">No subtasks yet.</p> : null}
            </div>
          </div>

          <div className="mt-8 border-t border-outline-variant pt-8">
            <h3 className="mb-3 font-mono text-xs font-bold uppercase tracking-wider text-on-surface-variant">Comments</h3>
            <div className="flex gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-full bg-primary text-sm font-bold text-white">ME</div>
              <input value={comment} onChange={(event) => setComment(event.target.value)} className="flex-1 rounded-xl border border-outline-variant bg-surface-container-low px-4 outline-none focus:border-primary" placeholder="Write a comment..." />
              <Button onClick={addComment} disabled={commentSaving}>{commentSaving ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}</Button>
            </div>
            <div className="mt-5 space-y-3">
              {comments.map((item) => (
                <div key={item.id} className="rounded-xl bg-surface-container-low p-4 text-sm">
                  <p className="font-semibold">{item.user.full_name}</p>
                  <p className="mt-1 text-on-surface-variant">{item.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <aside className="flex min-h-0 flex-col border-l border-outline-variant bg-surface-container-low">
          <div className="min-h-0 flex-1 space-y-6 overflow-y-auto p-6 pb-4">
            <div>
              <h3 className="mb-2 font-mono text-xs font-bold uppercase text-on-surface-variant">Status</h3>
              <select value={status} onChange={(event) => setStatus(event.target.value as ApiTask["status"])} className="w-full rounded-lg border border-outline-variant px-3 py-3 outline-none focus:border-primary">
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="review">Review</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div>
              <h3 className="mb-2 font-mono text-xs font-bold uppercase text-on-surface-variant">Priority</h3>
              <select value={priority} onChange={(event) => setPriority(event.target.value as ApiTask["priority"])} className="w-full rounded-lg border border-outline-variant px-3 py-3 outline-none focus:border-primary">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <h3 className="mb-2 flex items-center gap-2 font-mono text-xs font-bold uppercase text-on-surface-variant"><Calendar size={15} /> Due Date</h3>
              <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="w-full rounded-lg border border-outline-variant px-3 py-3 outline-none focus:border-primary" />
            </div>
            <label className="flex items-center justify-between rounded-xl border border-outline-variant bg-white p-4 text-sm font-semibold">
              Blocked
              <input type="checkbox" checked={isBlocked} onChange={(event) => setIsBlocked(event.target.checked)} />
            </label>
            {isBlocked ? <textarea value={blockedReason} onChange={(event) => setBlockedReason(event.target.value)} className="min-h-20 w-full rounded-lg border border-outline-variant p-3 text-sm outline-none focus:border-primary" placeholder="Blocked reason" /> : null}
            <div>
              <h3 className="mb-2 font-mono text-xs font-bold uppercase text-on-surface-variant">Assignee</h3>
              <select value={assignee} onChange={(event) => setAssignee(event.target.value ? Number(event.target.value) : "")} className="w-full rounded-lg border border-outline-variant px-3 py-3 outline-none focus:border-primary">
                <option value="">Unassigned</option>
                {currentUser ? <option value={currentUser.id}>Assign to me ({currentUser.full_name})</option> : null}
                {members.map((member) => (
                  <option value={member.user.id} key={member.id}>{member.user.full_name} - {member.role}</option>
                ))}
              </select>
            </div>
            <div className="rounded-xl border border-primary/20 bg-white p-5">
              <div className="mb-4 flex items-center gap-2 text-primary">
                <Bot size={20} />
                <h3 className="font-semibold">AI Task Assistant</h3>
              </div>
              <p className="text-sm text-on-surface-variant">AI is paused for now. This panel will be connected at the end.</p>
              <Button className="mt-5 w-full" disabled>AI Coming Later</Button>
            </div>
          </div>
          <div className="sticky bottom-0 border-t border-outline-variant bg-surface-container-low p-4">
            <Button onClick={save} className="w-full" disabled={saving}>
              {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
              {saving ? "Saving..." : "Save Task"}
            </Button>
            {message ? <p className="mt-2 text-center text-sm text-on-surface-variant">{message}</p> : null}
          </div>
        </aside>
      </section>
    </div>
  );
}
