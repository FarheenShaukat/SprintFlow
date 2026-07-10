"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Archive, Bot, CalendarDays, ExternalLink, FolderKanban, LockKeyhole, Pencil, Plus, Save, Trash2, Users, X } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RowSkeleton } from "@/components/ui/skeleton";
import { ApiError, authApi, projectApi, type Project, type ProjectMember, type User, type Workspace, type WorkspaceMember, workspaceApi } from "@/lib/api";

type ProjectRole = "admin" | "member" | "viewer";

export default function WorkspacePage() {
  const params = useParams<{ id: string }>();
  const workspaceId = Number(params.id);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [accessProject, setAccessProject] = useState<Project | null>(null);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editStatus, setEditStatus] = useState<Project["status"]>("active");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [user, workspaceList, projectList, memberList] = await Promise.all([
        authApi.me(),
        workspaceApi.list(),
        projectApi.list(workspaceId),
        workspaceApi.members(workspaceId)
      ]);
      setCurrentUser(user);
      setWorkspace(workspaceList.results.find((item) => item.id === workspaceId) ?? null);
      setProjects(projectList.results);
      setMembers(memberList.results);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not load workspace projects.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (workspaceId) void load();
  }, [workspaceId]);

  async function createProject() {
    if (!projectName.trim()) return;
    setError("");
    try {
      await projectApi.create(workspaceId, { name: projectName, description: projectDescription, status: "active" });
      setProjectName("");
      setProjectDescription("");
      setShowCreateModal(false);
      await load();
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not create project.");
    }
  }

  function startEdit(project: Project) {
    setEditingProjectId(project.id);
    setEditName(project.name);
    setEditDescription(project.description || "");
    setEditStatus(project.status);
  }

  async function saveProject(projectId: number) {
    if (!editName.trim()) return;
    setError("");
    try {
      await projectApi.update(projectId, { name: editName, description: editDescription, status: editStatus });
      setEditingProjectId(null);
      await load();
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not update project.");
    }
  }

  async function archiveProject(project: Project) {
    setError("");
    try {
      await projectApi.update(project.id, { status: project.status === "archived" ? "active" : "archived" });
      await load();
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not update project status.");
    }
  }

  async function deleteProject(project: Project) {
    if (!window.confirm(`Delete "${project.name}"? This will remove its tasks too.`)) return;
    setError("");
    try {
      await projectApi.remove(project.id);
      await load();
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not delete project.");
    }
  }

  async function openAccess(project: Project) {
    setAccessProject(project);
    setProjectMembers([]);
    try {
      const result = await projectApi.members(project.id);
      setProjectMembers(result.results);
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not load project access.");
    }
  }

  async function setMemberAccess(member: WorkspaceMember, role: ProjectRole | "") {
    if (!accessProject) return;
    const existing = projectMembers.find((item) => item.user.id === member.user.id);
    try {
      if (!role && existing) {
        await projectApi.removeMember(accessProject.id, existing.id);
      } else if (role && existing) {
        await projectApi.updateMember(accessProject.id, existing.id, { role });
      } else if (role) {
        await projectApi.addMember(accessProject.id, { user_id: member.user.id, role });
      }
      const result = await projectApi.members(accessProject.id);
      setProjectMembers(result.results);
      await load();
    } catch (error) {
      setError(error instanceof ApiError ? error.message : "Could not update project access.");
    }
  }

  const myMembership = members.find((member) => member.user.id === currentUser?.id);
  const canManageProjects = myMembership?.role === "owner" || myMembership?.role === "admin";
  const canUseSprintFlowAi = canManageProjects || projects.some((project) => project.user_project_role === "admin");
  const canCreateProjects = canManageProjects || Boolean(workspace?.allow_member_create_projects);
  const activeProjects = projects.filter((project) => project.status === "active").length;
  const archivedProjects = projects.filter((project) => project.status === "archived").length;
  const accessByUserId = useMemo(() => new Map(projectMembers.map((item) => [item.user.id, item])), [projectMembers]);

  return (
    <AppShell active="Projects">
      <div className="mx-auto max-w-7xl space-y-5 p-5">
        {error ? <div className="rounded-lg border border-error/20 bg-error-container p-3 text-sm text-error">{error}</div> : null}

        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-wider text-on-surface-variant">Workspace</p>
            <h1 className="text-2xl font-bold">{workspace?.name ?? "Workspace"}</h1>
            <p className="mt-1 text-sm text-on-surface-variant">{workspace?.description || "Manage projects and member access."}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {canCreateProjects ? <Button onClick={() => setShowCreateModal(true)}><Plus size={18} /> New Project</Button> : null}
            {canUseSprintFlowAi ? <Link href={`/workspace/${workspaceId}/sprintflow-ai`}><Button variant="secondary"><Bot size={18} /> SprintFlow AI</Button></Link> : null}
            <Link href="/team"><Button variant="secondary"><Users size={18} /> Team</Button></Link>
          </div>
        </div>

        <section className="grid gap-3 md:grid-cols-3">
          {[
            ["Active Projects", activeProjects, FolderKanban],
            ["Team Members", members.length, Users],
            ["Archived", archivedProjects, CalendarDays]
          ].map(([label, value, Icon]) => (
            <div key={String(label)} className="rounded-lg border border-outline-variant bg-surface p-4">
              <div className="flex items-center justify-between text-sm text-on-surface-variant">{String(label)}{typeof Icon !== "number" ? <Icon size={18} /> : null}</div>
              <strong className="mt-2 block text-2xl">{String(value)}</strong>
            </div>
          ))}
        </section>

        <section className="rounded-xl border border-outline-variant bg-surface p-5">
          <div className="mb-3 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-lg font-semibold">Projects</h2>
              <p className="mt-1 text-sm text-on-surface-variant">Admins see all projects. Members only see assigned projects.</p>
            </div>
            <Badge>{projects.length} visible</Badge>
          </div>

          {loading ? Array.from({ length: 3 }).map((_, index) => <RowSkeleton key={index} />) : projects.map((project) => {
            const isEditing = editingProjectId === project.id;
            return (
              <div key={project.id} className="border-t border-outline-variant py-3 first:border-t-0">
                {isEditing ? (
                  <div className="grid gap-3 lg:grid-cols-[1fr_1fr_180px_auto] lg:items-center">
                    <input value={editName} onChange={(event) => setEditName(event.target.value)} className="rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary" />
                    <input value={editDescription} onChange={(event) => setEditDescription(event.target.value)} className="rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Description" />
                    <select value={editStatus} onChange={(event) => setEditStatus(event.target.value as Project["status"])} className="rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary">
                      <option value="active">Active</option>
                      <option value="completed">Completed</option>
                      <option value="archived">Archived</option>
                    </select>
                    <div className="flex gap-2">
                      <Button onClick={() => saveProject(project.id)}><Save size={16} /> Save</Button>
                      <Button variant="secondary" onClick={() => setEditingProjectId(null)}><X size={16} /> Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <Link href={`/projects/${project.id}/board`} className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold">{project.name}</h3>
                        <Badge tone={project.status === "active" ? "primary" : project.status === "completed" ? "success" : "low"}>{project.status}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-on-surface-variant">{project.task_count} tasks - {project.description || "No description"}</p>
                    </Link>
                    <div className="flex flex-wrap gap-2">
                      <Link href={`/projects/${project.id}/board`}><Button variant="secondary"><ExternalLink size={16} /> Board</Button></Link>
                      {canManageProjects ? (
                        <>
                          <Button variant="secondary" onClick={() => openAccess(project)}><LockKeyhole size={16} /> Access</Button>
                          <Button variant="secondary" onClick={() => startEdit(project)}><Pencil size={16} /> Edit</Button>
                          <Button variant="secondary" onClick={() => archiveProject(project)}><Archive size={16} /> {project.status === "archived" ? "Restore" : "Archive"}</Button>
                          <Button variant="danger" onClick={() => deleteProject(project)}><Trash2 size={16} /> Delete</Button>
                        </>
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {!loading && !projects.length ? <p className="rounded-lg bg-surface-container-low p-4 text-sm text-on-surface-variant">No visible projects yet.</p> : null}
        </section>
      </div>

      {showCreateModal ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl border border-outline-variant bg-surface p-5 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">New Project</h2>
              <button onClick={() => setShowCreateModal(false)} className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container-low" aria-label="Close"><X size={18} /></button>
            </div>
            <label className="block text-sm font-medium">Name</label>
            <input value={projectName} onChange={(event) => setProjectName(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="Authentication Platform" />
            <label className="mt-4 block text-sm font-medium">Description</label>
            <textarea value={projectDescription} onChange={(event) => setProjectDescription(event.target.value)} className="mt-2 min-h-24 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="JWT auth, permissions, and protected routes" />
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={createProject} disabled={!projectName.trim()}><Plus size={18} /> Create</Button>
            </div>
          </div>
        </div>
      ) : null}

      {accessProject ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-2xl rounded-xl border border-outline-variant bg-surface p-5 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Project Access</h2>
                <p className="mt-1 text-sm text-on-surface-variant">{accessProject.name}</p>
              </div>
              <button onClick={() => setAccessProject(null)} className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container-low" aria-label="Close"><X size={18} /></button>
            </div>
            <div className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
              {members.map((member) => {
                const existing = accessByUserId.get(member.user.id);
                const isWorkspaceAdmin = member.role === "owner" || member.role === "admin";
                return (
                  <div key={member.id} className="flex flex-col gap-3 rounded-lg border border-outline-variant p-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h3 className="font-semibold">{member.user.full_name}</h3>
                      <p className="text-sm text-on-surface-variant">{member.user.email} - workspace {member.role}</p>
                    </div>
                    {isWorkspaceAdmin ? (
                      <Badge tone="success">All projects</Badge>
                    ) : (
                      <select value={existing?.role ?? ""} onChange={(event) => void setMemberAccess(member, event.target.value as ProjectRole | "")} className="rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary">
                        <option value="">No access</option>
                        <option value="viewer">Viewer</option>
                        <option value="member">Member</option>
                        <option value="admin">Project admin</option>
                      </select>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
