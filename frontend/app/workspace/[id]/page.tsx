"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CalendarDays, FolderKanban, Plus, Users } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CardSkeleton, RowSkeleton } from "@/components/ui/skeleton";
import { projectApi, type Project, type Workspace, type WorkspaceMember, workspaceApi } from "@/lib/api";

export default function WorkspacePage() {
  const params = useParams<{ id: string }>();
  const workspaceId = Number(params.id);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const [workspaceList, projectList, memberList] = await Promise.all([
      workspaceApi.list(),
      projectApi.list(workspaceId),
      workspaceApi.members(workspaceId)
    ]);
    setWorkspace(workspaceList.results.find((item) => item.id === workspaceId) ?? null);
    setProjects(projectList.results);
    setMembers(memberList.results);
    setLoading(false);
  }

  useEffect(() => {
    if (workspaceId) void load();
  }, [workspaceId]);

  async function createProject() {
    if (!projectName.trim()) return;
    await projectApi.create(workspaceId, { name: projectName, description: projectDescription, status: "active" });
    setProjectName("");
    setProjectDescription("");
    await load();
  }

  return (
    <AppShell active="Projects">
      <div className="mx-auto max-w-7xl space-y-6 p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-wider text-on-surface-variant">Workspace</p>
            <h1 className="text-3xl font-bold">{workspace?.name ?? "Workspace"}</h1>
            <p className="mt-2 text-on-surface-variant">{workspace?.description || "Create projects and invite members from here."}</p>
          </div>
          <Link href="/team"><Button variant="secondary"><Users size={18} /> Manage Team</Button></Link>
        </div>
        <section className="grid gap-4 md:grid-cols-3">
          {loading ? Array.from({ length: 3 }).map((_, index) => <CardSkeleton key={index} />) : [
            ["Active Projects", projects.length, FolderKanban],
            ["Team Members", members.length, Users],
            ["Open Sprints", 0, CalendarDays]
          ].map(([label, value, Icon]) => (
            <div key={String(label)} className="glass-card rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between text-on-surface-variant">{String(label)}{typeof Icon !== "number" ? <Icon /> : null}</div>
              <strong className="text-4xl">{String(value)}</strong>
            </div>
          ))}
        </section>
        <section className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="rounded-2xl border border-outline-variant bg-surface p-6">
            <h2 className="mb-4 text-xl font-semibold">Projects</h2>
            {loading ? Array.from({ length: 3 }).map((_, index) => <RowSkeleton key={index} />) : projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}/board`} className="flex items-center justify-between border-t border-outline-variant py-4 first:border-t-0">
                <div><h3 className="font-semibold">{project.name}</h3><p className="text-sm text-on-surface-variant">{project.task_count} tasks · {project.description || "No description"}</p></div>
                <Badge tone="primary">{project.status}</Badge>
              </Link>
            ))}
            {!projects.length ? <p className="rounded-xl bg-surface-container-low p-5 text-sm text-on-surface-variant">No projects yet. Create one to open a Kanban board.</p> : null}
          </div>
          <div className="rounded-2xl border border-outline-variant bg-surface p-6">
            <h2 className="text-xl font-semibold">Create Project</h2>
            <label className="mt-5 block text-sm font-medium">Name</label>
            <input value={projectName} onChange={(event) => setProjectName(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="Authentication Platform" />
            <label className="mt-4 block text-sm font-medium">Description</label>
            <textarea value={projectDescription} onChange={(event) => setProjectDescription(event.target.value)} className="mt-2 min-h-24 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="JWT auth, permissions, and protected routes" />
            <Button onClick={createProject} className="mt-5 w-full"><Plus size={18} /> Create Project</Button>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
