"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, HeartPulse, Plus, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CardSkeleton, RowSkeleton } from "@/components/ui/skeleton";
import { projectApi, reportApi, type Project, type ProjectReport, type Workspace, workspaceApi } from "@/lib/api";

export default function DashboardPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [report, setReport] = useState<ProjectReport | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const workspaceResult = await workspaceApi.list();
      setWorkspaces(workspaceResult.results);
      const firstWorkspace = workspaceResult.results[0];
      if (firstWorkspace) {
        const projectResult = await projectApi.list(firstWorkspace.id);
        setProjects(projectResult.results);
        const firstProject = projectResult.results[0];
        setReport(firstProject ? await reportApi.get(firstProject.id) : null);
      }
    } catch {
      setError("Sign in first, then create your workspace.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function createWorkspace() {
    if (!name.trim()) return;
    await workspaceApi.create({ name, description });
    setName("");
    setDescription("");
    await load();
  }

  const metrics = [
    { label: "Sprint Health", value: report ? `${report.sprint_health_score}%` : "0%", icon: HeartPulse, note: "Live report" },
    { label: "Tasks Completed", value: report?.completed_tasks ?? 0, icon: CheckCircle2, note: `${report?.total_tasks ?? 0} total` },
    { label: "Blocked Issues", value: report?.blocked_tasks ?? 0, icon: AlertCircle, note: "Needs attention" },
    { label: "Velocity", value: `${report?.completion_rate ?? 0}%`, icon: TrendingUp, note: "Completion rate" }
  ];

  return (
    <AppShell active="Dashboard">
      <div className="mx-auto max-w-7xl space-y-8 p-6">
        {error ? <div className="rounded-xl border border-error/20 bg-error-container p-4 text-sm text-error">{error}</div> : null}
        <section className="grid gap-4 md:grid-cols-4">
          {loading ? Array.from({ length: 4 }).map((_, index) => <CardSkeleton key={index} />) : metrics.map((metric) => {
            const Icon = metric.icon;
            return (
              <div key={metric.label} className="glass-card rounded-xl p-5">
                <div className="mb-4 flex items-center justify-between text-sm text-on-surface-variant"><span>{metric.label}</span><Icon className="text-primary" size={20} /></div>
                <div className="text-4xl font-bold text-on-surface">{metric.value}</div>
                <p className="mt-1 text-xs font-medium text-on-surface-variant">{metric.note}</p>
              </div>
            );
          })}
        </section>

        <section className="grid gap-8 lg:grid-cols-[1fr_380px]">
          <div className="rounded-2xl border border-outline-variant bg-surface p-6">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Workspaces</h2>
              <Badge>{loading ? "Loading" : `${workspaces.length} total`}</Badge>
            </div>
            <div className="space-y-3">
              {loading ? Array.from({ length: 3 }).map((_, index) => <RowSkeleton key={index} />) : workspaces.map((workspace) => (
                <Link href={`/workspace/${workspace.id}`} key={workspace.id} className="flex items-center justify-between rounded-xl border border-outline-variant p-4 transition hover:border-primary">
                  <div>
                    <h3 className="font-semibold">{workspace.name}</h3>
                    <p className="text-sm text-on-surface-variant">{workspace.description || "No description yet"} · {workspace.member_count} members</p>
                  </div>
                  <Button variant="secondary" type="button">Open</Button>
                </Link>
              ))}
              {!loading && workspaces.length === 0 ? <p className="rounded-xl bg-surface-container-low p-5 text-sm text-on-surface-variant">No workspace yet. Create your first workspace from the form.</p> : null}
            </div>
          </div>

          <div className="rounded-2xl border border-outline-variant bg-surface p-6">
            <h2 className="text-2xl font-semibold">Create Workspace</h2>
            <label className="mt-5 block text-sm font-medium">Name</label>
            <input value={name} onChange={(event) => setName(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="Engineering" />
            <label className="mt-4 block text-sm font-medium">Description</label>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} className="mt-2 min-h-24 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="Product engineering workspace" />
            <Button onClick={createWorkspace} className="mt-5 w-full"><Plus size={18} /> Create Workspace</Button>
          </div>
        </section>

        {projects.length ? (
          <section className="rounded-2xl border border-outline-variant bg-surface p-6">
            <h2 className="mb-4 text-xl font-semibold">Recent Projects</h2>
            <div className="grid gap-3 md:grid-cols-3">
              {projects.slice(0, 3).map((project) => (
                <Link href={`/projects/${project.id}/board`} key={project.id} className="rounded-xl border border-outline-variant p-4 hover:border-primary">
                  <h3 className="font-semibold">{project.name}</h3>
                  <p className="mt-2 text-sm text-on-surface-variant">{project.description || "No description"} · {project.task_count} tasks</p>
                </Link>
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}
