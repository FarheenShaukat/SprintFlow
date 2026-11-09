"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Mail } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RowSkeleton } from "@/components/ui/skeleton";
import { authApi, type User, type Workspace, type WorkspaceInvitation, type WorkspaceMember, workspaceApi } from "@/lib/api";

export default function TeamPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState<number | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"admin" | "member">("member");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [invitationError, setInvitationError] = useState("");
  const [loading, setLoading] = useState(true);
  const [inviting, setInviting] = useState(false);
  const loadRequest = useRef(0);

  const workspace = workspaces.find((item) => item.id === workspaceId);
  const myRole = members.find((member) => member.user.id === currentUser?.id)?.role;
  const canManage = myRole === "owner" || myRole === "admin";
  const canInvite = canManage || (myRole === "member" && Boolean(workspace?.allow_member_invite_members));

  async function load(selectedId?: number) {
    const requestId = ++loadRequest.current;
    setLoading(true);
    setInviting(false);
    setError("");
    setInvitationError("");
    setMessage("");
    setMembers([]);
    setInvitations([]);
    setRole("member");
    if (selectedId !== undefined) {
      setWorkspaceId(selectedId);
      setEmail("");
      setFullName("");
    }
    try {
      const [workspaceResult, user] = await Promise.all([workspaceApi.list(), authApi.me()]);
      if (requestId !== loadRequest.current) return;
      setWorkspaces(workspaceResult.results);
      setCurrentUser(user);
      const id = selectedId ?? workspaceId ?? workspaceResult.results[0]?.id ?? null;
      setWorkspaceId(id);
      if (!id) return;
      const memberResult = await workspaceApi.members(id);
      if (requestId !== loadRequest.current) return;
      setMembers(memberResult.results);
      const role = memberResult.results.find((member) => member.user.id === user.id)?.role;
      if (role === "owner" || role === "admin") {
        try {
          const invitationResult = await workspaceApi.invitations(id);
          if (requestId === loadRequest.current) setInvitations(invitationResult.results);
        } catch (error) {
          if (requestId === loadRequest.current) setInvitationError(error instanceof Error ? error.message : "Could not load invitations. Please try again.");
        }
      }
    } catch (error) {
      if (requestId === loadRequest.current) setError(error instanceof Error ? error.message : "Could not load your team. Please try again.");
    } finally {
      if (requestId === loadRequest.current) setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    return () => { loadRequest.current++; };
  }, []);

  async function invite() {
    if (!workspaceId || !email.trim() || !canInvite || inviting || loading) return;
    const requestId = loadRequest.current;
    setInviting(true);
    setError("");
    setMessage("");
    try {
      const invitation = await workspaceApi.invite(workspaceId, { email: email.trim(), full_name: fullName.trim(), role: canManage ? role : "member" });
      if (requestId !== loadRequest.current) return;
      setEmail("");
      setFullName("");
      setRole("member");
      setMessage(invitation.email_sent ? "Invite sent. It will stay pending until the recipient accepts." : `Invite saved as pending, but email failed: ${invitation.email_error || "Please try sending it again."}`);
      if (canManage) setInvitations((current) => [invitation, ...current.filter((item) => item.id !== invitation.id)]);
    } catch (error) {
      if (requestId === loadRequest.current) setError(error instanceof Error ? error.message : "Could not send invitation. Please try again.");
    } finally {
      if (requestId === loadRequest.current) setInviting(false);
    }
  }

  return (
    <AppShell active="Team">
      <div className="mx-auto max-w-7xl space-y-6 p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div><p className="font-mono text-xs uppercase tracking-wider text-on-surface-variant">Members & Roles</p><h1 className="text-3xl font-bold">Team Members</h1></div>
          <select aria-label="Workspace" value={workspaceId ?? ""} onChange={(event) => void load(Number(event.target.value))} className="rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary">
            {workspaces.map((workspace) => <option value={workspace.id} key={workspace.id}>{workspace.name}</option>)}
          </select>
        </div>
        {error ? <div role="alert" className="rounded-lg border border-error/20 bg-error-container p-3 text-sm text-error">{error} <Button variant="secondary" onClick={() => void load(workspaceId ?? undefined)} disabled={loading}>Retry</Button></div> : null}
        <div className="rounded-lg border border-outline-variant bg-surface p-4 text-sm text-on-surface-variant">
          Invite your teammate to this workspace first. After they accept, a workspace owner or admin can open the workspace and choose Manage Access on a project to give them access to the same board.
          {workspaceId ? <Link href={`/workspace/${workspaceId}`} className="ml-2 font-medium text-primary underline focus-visible:outline focus-visible:outline-2">Open workspace</Link> : null}
        </div>
        {!loading && !error && !workspaces.length ? <p className="text-sm text-on-surface-variant">No workspaces yet. Create a workspace from the dashboard to start collaborating.</p> : null}
        <section className="grid gap-6 lg:grid-cols-[1fr_380px]">
          <div className="rounded-2xl border border-outline-variant bg-surface">
            <div className="border-b border-outline-variant p-5">
              <h2 className="text-lg font-semibold">Members</h2>
            </div>
            {loading ? Array.from({ length: 3 }).map((_, index) => <RowSkeleton key={index} />) : members.map((member) => (
              <div className="grid gap-4 border-t border-outline-variant p-5 first:border-t-0 md:grid-cols-[1fr_140px]" key={member.id}>
                <div className="flex items-center gap-4"><div className="grid h-11 w-11 place-items-center rounded-full bg-primary/10 font-bold text-primary">{member.user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}</div><div><h2 className="font-semibold">{member.user.full_name}</h2><p className="text-sm text-on-surface-variant">{member.user.email}</p></div></div>
                <Badge tone={member.role === "owner" ? "primary" : "medium"}>{member.role}</Badge>
              </div>
            ))}
            {!loading && !error && !members.length ? <p className="p-6 text-sm text-on-surface-variant">No members to display.</p> : null}
            {canManage ? <>
            <div className="border-y border-outline-variant p-5">
              <h2 className="text-lg font-semibold">Invitations</h2>
            </div>
            {invitationError ? <p role="alert" className="p-5 text-sm text-error">Could not load invitations: {invitationError} <Button variant="secondary" onClick={() => void load(workspaceId ?? undefined)}>Retry</Button></p> : null}
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
            {!loading && !invitationError && !invitations.length ? <p className="p-6 text-sm text-on-surface-variant">No invitations yet.</p> : null}
            </> : null}
          </div>
          {canInvite && !loading ? <form onSubmit={(event) => { event.preventDefault(); void invite(); }} className="rounded-2xl border border-outline-variant bg-surface p-6">
            <h2 className="text-xl font-semibold">Invite Member</h2>
            <label htmlFor="invite-email" className="mt-5 block text-sm font-medium">Email</label>
            <input id="invite-email" type="email" required disabled={inviting} value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="teammate@example.com" />
            <label htmlFor="invite-name" className="mt-4 block text-sm font-medium">Full name</label>
            <input id="invite-name" disabled={inviting} value={fullName} onChange={(event) => setFullName(event.target.value)} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" placeholder="Optional" />
            {canManage ? <>
            <label htmlFor="invite-role" className="mt-4 block text-sm font-medium">Role</label>
            <select id="invite-role" disabled={inviting} value={role} onChange={(event) => setRole(event.target.value as "admin" | "member")} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary">
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            </> : <p className="mt-4 text-sm text-on-surface-variant">Teammates you invite join as workspace members.</p>}
            <Button type="submit" disabled={inviting || !email.trim()} className="mt-5 w-full"><Mail size={18} /> {inviting ? "Sending invite..." : "Send Invite"}</Button>
            {message ? <p role="status" className="mt-4 rounded-lg bg-surface-container-low p-3 text-sm text-on-surface-variant">{message}</p> : null}
          </form> : !loading && myRole ? <div className="rounded-2xl border border-outline-variant bg-surface p-6 text-sm text-on-surface-variant">Ask a workspace owner or admin to invite your teammate and grant project access.</div> : null}
        </section>
      </div>
    </AppShell>
  );
}
