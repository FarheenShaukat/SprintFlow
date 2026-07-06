"use client";

import { useEffect, useState } from "react";
import { Mail, Shield } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RowSkeleton } from "@/components/ui/skeleton";
import { type Workspace, type WorkspaceInvitation, type WorkspaceMember, workspaceApi } from "@/lib/api";

export default function TeamPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState<number | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"admin" | "member">("member");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  async function load(selectedId?: number) {
    setLoading(true);
    const workspaceResult = await workspaceApi.list();
    setWorkspaces(workspaceResult.results);
    const id = selectedId ?? workspaceId ?? workspaceResult.results[0]?.id ?? null;
    setWorkspaceId(id);
    if (id) {
      const [memberResult, invitationResult] = await Promise.all([
        workspaceApi.members(id),
        workspaceApi.invitations(id)
      ]);
      setMembers(memberResult.results);
      setInvitations(invitationResult.results);
    }
    setLoading(false);
  }

  useEffect(() => {
    void load();
  }, []);

  async function invite() {
    if (!workspaceId || !email.trim()) return;
    const invitation = await workspaceApi.invite(workspaceId, { email, full_name: fullName, role });
    setEmail("");
    setFullName("");
    setRole("member");
    setMessage(invitation.email_sent ? "Invite sent. It will stay pending until the recipient accepts." : `Invite saved as pending, but email failed: ${invitation.email_error}`);
    await load(workspaceId);
  }

  return (
    <AppShell active="Team">
      <div className="mx-auto max-w-7xl space-y-6 p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div><p className="font-mono text-xs uppercase tracking-wider text-on-surface-variant">Members & Roles</p><h1 className="text-3xl font-bold">Team Members</h1></div>
          <select value={workspaceId ?? ""} onChange={(event) => void load(Number(event.target.value))} className="rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary">
            {workspaces.map((workspace) => <option value={workspace.id} key={workspace.id}>{workspace.name}</option>)}
          </select>
        </div>
        <section className="grid gap-6 lg:grid-cols-[1fr_380px]">
          <div className="rounded-2xl border border-outline-variant bg-surface">
            <div className="border-b border-outline-variant p-5">
              <h2 className="text-lg font-semibold">Members</h2>
            </div>
            {loading ? Array.from({ length: 3 }).map((_, index) => <RowSkeleton key={index} />) : members.map((member) => (
              <div className="grid gap-4 border-t border-outline-variant p-5 first:border-t-0 md:grid-cols-[1fr_140px_120px]" key={member.id}>
                <div className="flex items-center gap-4"><div className="grid h-11 w-11 place-items-center rounded-full bg-primary/10 font-bold text-primary">{member.user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}</div><div><h2 className="font-semibold">{member.user.full_name}</h2><p className="text-sm text-on-surface-variant">{member.user.email}</p></div></div>
                <Badge tone={member.role === "owner" ? "primary" : "medium"}>{member.role}</Badge>
                <Button variant="secondary"><Shield size={16} /> Role</Button>
              </div>
            ))}
            {!members.length ? <p className="p-6 text-sm text-on-surface-variant">No members yet. Invite someone from the form.</p> : null}
            <div className="border-y border-outline-variant p-5">
              <h2 className="text-lg font-semibold">Invitations</h2>
            </div>
            {loading ? Array.from({ length: 2 }).map((_, index) => <RowSkeleton key={index} />) : invitations.map((invitation) => (
              <div className="grid gap-4 border-t border-outline-variant p-5 first:border-t-0 md:grid-cols-[1fr_120px_130px]" key={invitation.id}>
                <div>
                  <h2 className="font-semibold">{invitation.full_name || invitation.email}</h2>
                  <p className="text-sm text-on-surface-variant">{invitation.email}</p>
                  {!invitation.email_sent && invitation.email_error ? <p className="mt-1 text-xs text-error">Email failed: {invitation.email_error}</p> : null}
                </div>
                <Badge tone={invitation.status === "accepted" ? "success" : "medium"}>{invitation.status}</Badge>
                <Badge tone={invitation.email_sent ? "success" : "critical"}>{invitation.email_sent ? "email sent" : "email failed"}</Badge>
              </div>
            ))}
            {!invitations.length ? <p className="p-6 text-sm text-on-surface-variant">No invitations yet.</p> : null}
          </div>
          <div className="rounded-2xl border border-outline-variant bg-surface p-6">
            <h2 className="text-xl font-semibold">Invite Member</h2>
            <label className="mt-5 block text-sm font-medium">Email</label>
            <input value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="teammate@example.com" />
            <label className="mt-4 block text-sm font-medium">Full name</label>
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="Optional" />
            <label className="mt-4 block text-sm font-medium">Role</label>
            <select value={role} onChange={(event) => setRole(event.target.value as "admin" | "member")} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary">
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <Button onClick={invite} className="mt-5 w-full"><Mail size={18} /> Send Invite</Button>
            {message ? <p className="mt-4 rounded-lg bg-surface-container-low p-3 text-sm text-on-surface-variant">{message}</p> : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
