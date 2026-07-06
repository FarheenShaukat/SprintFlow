import { AlertTriangle, CalendarClock, MessageSquare, Paperclip } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Task } from "@/types/domain";

export function TaskCard({ task, onOpen }: { task: Task; onOpen?: (task: Task) => void }) {
  return (
    <button onClick={() => onOpen?.(task)} className="w-full rounded-xl border border-outline-variant bg-surface p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft">
      <div className="mb-3 flex items-start justify-between gap-3">
        <Badge tone={task.priority === "critical" ? "critical" : task.priority}>{task.priority}</Badge>
        <span className="font-mono text-xs text-on-surface-variant">{task.key}</span>
      </div>
      <h3 className="text-base font-semibold leading-snug">{task.title}</h3>
      {task.isBlocked ? (
        <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-error">
          <AlertTriangle size={15} /> Blocked
        </div>
      ) : null}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs text-on-surface-variant">
          <span className="flex items-center gap-1"><MessageSquare size={15} /> {task.comments}</span>
          <span className="flex items-center gap-1"><Paperclip size={15} /> {task.attachments}</span>
          <span className="flex items-center gap-1"><CalendarClock size={15} /> {task.dueDate}</span>
        </div>
        <div className="grid h-7 w-7 place-items-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">{task.assignee.fullName.split(" ").map((n) => n[0]).join("").slice(0, 2)}</div>
      </div>
      <div className="mt-3 flex items-center justify-between rounded-lg bg-surface-container-low px-2 py-1 text-xs">
        <span className="text-on-surface-variant">AI risk</span>
        <span className={task.aiRiskScore > 75 ? "font-bold text-error" : "font-bold text-primary"}>{task.aiRiskScore}%</span>
      </div>
    </button>
  );
}
