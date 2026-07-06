"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, HeartPulse, ShieldAlert } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { CardSkeleton } from "@/components/ui/skeleton";
import { PriorityChart, VelocityChart } from "@/components/reports-chart";
import { projectApi, reportApi, type Project, type ProjectReport, workspaceApi } from "@/lib/api";

export default function ReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | null>(null);
  const [report, setReport] = useState<ProjectReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load(selectedProjectId?: number) {
    setLoading(true);
    try {
      const workspaces = await workspaceApi.list();
      const firstWorkspace = workspaces.results[0];
      if (!firstWorkspace) {
        setProjects([]);
        setReport(null);
        return;
      }
      const projectResult = await projectApi.list(firstWorkspace.id);
      setProjects(projectResult.results);
      const id = selectedProjectId ?? projectId ?? projectResult.results[0]?.id ?? null;
      setProjectId(id);
      setReport(id ? await reportApi.get(id) : null);
      setError("");
    } catch {
      setError("Could not load reports. Sign in and create a project first.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const priorityData = useMemo(
    () => report?.tasks_by_priority.map((item) => ({ name: item.priority, tasks: item.count })) ?? [],
    [report]
  );

  return (
    <AppShell active="Reports">
      <div className="mx-auto max-w-7xl space-y-6 p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-wider text-on-surface-variant">Reports / Analytics</p>
            <h1 className="text-3xl font-bold">Sprint Intelligence</h1>
          </div>
          <select value={projectId ?? ""} onChange={(event) => void load(Number(event.target.value))} className="rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary">
            {projects.map((project) => <option value={project.id} key={project.id}>{project.name}</option>)}
          </select>
        </div>
        {error ? <div className="rounded-xl border border-error/20 bg-error-container p-4 text-sm text-error">{error}</div> : null}
        <section className="grid gap-4 md:grid-cols-4">
          {loading ? Array.from({ length: 4 }).map((_, index) => <CardSkeleton key={index} />) : [
            ["Sprint Health", `${report?.sprint_health_score ?? 0}%`],
            ["Completed", report?.completed_tasks ?? 0],
            ["Overdue", report?.overdue_tasks ?? 0],
            ["Blocked", report?.blocked_tasks ?? 0]
          ].map(([label, value]) => (
            <div key={label} className="glass-card rounded-xl p-5"><p className="text-sm text-on-surface-variant">{label}</p><strong className="mt-3 block text-4xl">{value}</strong></div>
          ))}
        </section>
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-outline-variant bg-surface p-6"><h2 className="mb-5 text-xl font-semibold">Velocity & Health</h2><VelocityChart /></div>
          <div className="rounded-2xl border border-outline-variant bg-surface p-6"><h2 className="mb-5 text-xl font-semibold">Tasks by Priority</h2><PriorityChart data={priorityData} /></div>
        </section>
        <section className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="rounded-2xl border border-primary/20 bg-surface p-6">
            <div className="mb-4 flex items-center gap-3 text-primary"><Bot /><h2 className="text-xl font-semibold">AI Sprint Summary</h2></div>
            <p className="leading-7 text-on-surface-variant">AI is intentionally disabled for now. This panel will connect to `/api/ai/sprint-summary/` at the end after the core product workflow is stable.</p>
          </div>
          <div className="rounded-2xl border border-outline-variant bg-surface p-6">
            <div className="mb-4 flex items-center gap-3"><HeartPulse className="text-primary" /><h2 className="text-xl font-semibold">Health Rules</h2></div>
            <div className="space-y-2 text-sm text-on-surface-variant">
              <p>-5 each overdue task</p><p>-7 each blocked task</p><p>-3 critical pending task</p><p>+5 completion above 80%</p>
            </div>
            <Badge className="mt-5" tone="success"><ShieldAlert size={14} /> Score clamped 0-100</Badge>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
