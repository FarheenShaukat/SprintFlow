"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { RowSkeleton } from "@/components/ui/skeleton";
import { api, authApi, type Workspace, workspaceApi } from "@/lib/api";

export default function SettingsPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authApi.me().then((user) => {
      setFullName(user.full_name);
      setEmail(user.email);
      setAvatarUrl(user.avatar_url);
    }).catch(() => setMessage("Sign in to edit your profile."));
    workspaceApi.list().then((result) => {
      setWorkspaces(result.results);
      setWorkspace(result.results[0] ?? null);
    }).catch(() => undefined).finally(() => setLoading(false));
  }, []);

  async function save() {
    await api("/auth/me/", {
      method: "PATCH",
      body: JSON.stringify({ full_name: fullName, email, avatar_url: avatarUrl })
    });
    setMessage("Profile saved.");
  }

  async function saveWorkspaceSettings() {
    if (!workspace) return;
    const updated = await workspaceApi.update(workspace.id, workspace);
    setWorkspace(updated);
    setWorkspaces((current) => current.map((item) => item.id === updated.id ? updated : item));
    setMessage("Workspace settings saved.");
  }

  function setPermission(key: keyof Pick<Workspace, "allow_member_create_projects" | "allow_member_create_tasks" | "allow_member_edit_tasks" | "allow_member_comment" | "allow_member_upload_attachments" | "allow_member_invite_members">, value: boolean) {
    setWorkspace((current) => current ? { ...current, [key]: value } : current);
  }

  return (
    <AppShell active="Settings">
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div><p className="font-mono text-xs uppercase tracking-wider text-on-surface-variant">Settings / Profile</p><h1 className="text-3xl font-bold">Profile Settings</h1></div>
        <section className="rounded-2xl border border-outline-variant bg-surface p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm font-medium">Full name<input value={fullName} onChange={(event) => setFullName(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" /></label>
            <label className="text-sm font-medium">Email<input value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" /></label>
            <label className="text-sm font-medium md:col-span-2">Avatar URL<input value={avatarUrl} onChange={(event) => setAvatarUrl(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="https://..." /></label>
          </div>
          <Button onClick={save} className="mt-6"><Save size={18} /> Save Changes</Button>
          {message ? <p className="mt-4 text-sm text-on-surface-variant">{message}</p> : null}
        </section>
        <section className="rounded-2xl border border-outline-variant bg-surface p-6">
          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
            <h2 className="text-xl font-semibold">Workspace Permissions</h2>
            <select value={workspace?.id ?? ""} onChange={(event) => setWorkspace(workspaces.find((item) => item.id === Number(event.target.value)) ?? null)} className="rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary">
              {workspaces.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
            </select>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {loading ? <><RowSkeleton /><RowSkeleton /></> : null}
            <label className="flex items-center justify-between rounded-lg border border-outline-variant p-4 text-sm">Members can create projects<input type="checkbox" checked={Boolean(workspace?.allow_member_create_projects)} onChange={(event) => setPermission("allow_member_create_projects", event.target.checked)} /></label>
            <label className="flex items-center justify-between rounded-lg border border-outline-variant p-4 text-sm">Members can create tasks<input type="checkbox" checked={Boolean(workspace?.allow_member_create_tasks)} onChange={(event) => setPermission("allow_member_create_tasks", event.target.checked)} /></label>
            <label className="flex items-center justify-between rounded-lg border border-outline-variant p-4 text-sm">Members can edit tasks<input type="checkbox" checked={Boolean(workspace?.allow_member_edit_tasks)} onChange={(event) => setPermission("allow_member_edit_tasks", event.target.checked)} /></label>
            <label className="flex items-center justify-between rounded-lg border border-outline-variant p-4 text-sm">Members can comment<input type="checkbox" checked={Boolean(workspace?.allow_member_comment)} onChange={(event) => setPermission("allow_member_comment", event.target.checked)} /></label>
            <label className="flex items-center justify-between rounded-lg border border-outline-variant p-4 text-sm">Members can upload attachments<input type="checkbox" checked={Boolean(workspace?.allow_member_upload_attachments)} onChange={(event) => setPermission("allow_member_upload_attachments", event.target.checked)} /></label>
            <label className="flex items-center justify-between rounded-lg border border-outline-variant p-4 text-sm">Members can invite members<input type="checkbox" checked={Boolean(workspace?.allow_member_invite_members)} onChange={(event) => setPermission("allow_member_invite_members", event.target.checked)} /></label>
          </div>
          <Button onClick={saveWorkspaceSettings} className="mt-6"><Save size={18} /> Save Workspace Settings</Button>
        </section>
      </div>
    </AppShell>
  );
}
