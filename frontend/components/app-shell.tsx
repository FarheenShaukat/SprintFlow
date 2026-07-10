"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertTriangle, BarChart3, Bolt, Bot, ChevronsLeft, ChevronsRight, ExternalLink, FolderKanban, LayoutDashboard, LogOut, MessageSquareText, Plus, Search, Send, Settings, X, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { clearAuthTokens, type Workspace, workspaceApi } from "@/lib/api";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/team", label: "Team", icon: Users },
  { href: "/reports", label: "Reports", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings }
];

export function AppShell({ children, active = "Dashboard" }: { children: React.ReactNode; active?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [showWorkspaceForm, setShowWorkspaceForm] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDescription, setWorkspaceDescription] = useState("");
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [fallbackWorkspace, setFallbackWorkspace] = useState<Workspace | null>(null);
  const [ready, setReady] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("sprintflow_access");
    if (!token) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    setReady(true);
  }, [pathname, router]);

  useEffect(() => {
    function handleSessionExpired() {
      setSessionExpired(true);
    }

    window.addEventListener("sprintflow:session-expired", handleSessionExpired);
    return () => window.removeEventListener("sprintflow:session-expired", handleSessionExpired);
  }, []);

  useEffect(() => {
    workspaceApi.list()
      .then((result) => setFallbackWorkspace(result.results[0] ?? null))
      .catch(() => setFallbackWorkspace(null));
  }, []);

  useEffect(() => {
    const match = pathname.match(/\/workspace\/(\d+)/);
    if (!match) {
      setCurrentWorkspace(null);
      return;
    }
    const workspaceId = Number(match[1]);
    workspaceApi.list()
      .then((result) => setCurrentWorkspace(result.results.find((workspace) => workspace.id === workspaceId) ?? null))
      .catch(() => setCurrentWorkspace(null));
  }, [pathname]);

  async function createWorkspace() {
    if (!workspaceName.trim()) return;
    const workspace = await workspaceApi.create({ name: workspaceName, description: workspaceDescription });
    setWorkspaceName("");
    setWorkspaceDescription("");
    setShowWorkspaceForm(false);
    router.push(`/workspace/${workspace.id}`);
  }

  function signOut() {
    clearAuthTokens();
    router.push("/login");
  }

  function signInAgain() {
    clearAuthTokens();
    router.push(`/login?next=${encodeURIComponent(pathname)}`);
  }

  const sprintAiWorkspace = currentWorkspace ?? fallbackWorkspace;

  if (!ready) {
    return <main className="grid min-h-screen place-items-center bg-background text-on-surface">Checking session...</main>;
  }

  return (
    <div className={cn("min-h-screen bg-background text-on-surface md:grid", collapsed ? "md:grid-cols-[76px_1fr]" : "md:grid-cols-[260px_1fr]")}>
      <aside className="sticky top-0 hidden h-screen min-h-0 border-r border-outline-variant bg-surface md:flex md:flex-col">
        <div className={cn("shrink-0 flex items-center gap-3 px-4 py-6", collapsed && "justify-center px-3")}>
          {collapsed ? (
            <button onClick={() => setCollapsed(false)} className="grid h-11 w-11 place-items-center rounded-lg bg-primary text-white shadow-sm" aria-label="Expand sidebar">
              <ChevronsRight size={20} />
            </button>
          ) : (
            <>
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-white">
                <Bolt size={21} />
              </div>
              <div className="min-w-0">
                <h1 className="truncate text-xl font-bold leading-none text-primary">SprintFlow AI</h1>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-on-surface-variant">SaaS Platform</p>
              </div>
              <button onClick={() => setCollapsed(true)} className="ml-auto rounded-lg p-2 text-on-surface-variant hover:bg-surface-container-low" aria-label="Collapse sidebar">
                <ChevronsLeft size={18} />
              </button>
            </>
          )}
        </div>
        <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto px-3 pb-4">
          {nav.map((item) => {
            const Icon = item.icon;
            const selected = item.label === active;
            return (
              <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 px-4 py-3 text-sm transition", selected ? "border-l-4 border-primary bg-primary/10 text-primary" : "rounded-lg text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface")}>
                <Icon size={20} />
                {!collapsed ? item.label : null}
              </Link>
            );
          })}
          {sprintAiWorkspace ? (
            <Link href={`/workspace/${sprintAiWorkspace.id}/sprintflow-ai`} className={cn("flex items-center gap-3 px-4 py-3 text-sm transition", pathname.includes("/sprintflow-ai") ? "border-l-4 border-primary bg-primary/10 text-primary" : "rounded-lg text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface")}>
              <Bot size={20} />
              {!collapsed ? "SprintAI" : null}
            </Link>
          ) : null}
          <button onClick={() => setShowWorkspaceForm((value) => !value)} className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-on-surface-variant transition hover:bg-surface-container-low hover:text-on-surface">
            <Plus size={20} />
            {!collapsed ? "Add Workspace" : null}
          </button>
          {showWorkspaceForm && !collapsed ? (
            <div className="rounded-xl border border-outline-variant bg-surface-container-low p-3">
              <input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} className="w-full rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Workspace name" />
              <textarea value={workspaceDescription} onChange={(event) => setWorkspaceDescription(event.target.value)} className="mt-2 min-h-16 w-full rounded-lg border border-outline-variant px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Description" />
              <Button onClick={createWorkspace} className="mt-2 w-full"><Plus size={16} /> Create</Button>
            </div>
          ) : null}
          <Link href="/dashboard" className="flex items-center gap-3 rounded-lg px-4 py-3 text-sm text-on-surface-variant transition hover:bg-surface-container-low hover:text-on-surface">
            <FolderKanban size={20} />
            {!collapsed ? "Workspaces" : null}
          </Link>
        </nav>
        <div className="shrink-0 space-y-3 border-t border-outline-variant bg-surface p-4">
          {currentWorkspace ? (
            <Link href={`/workspace/${currentWorkspace.id}`} className={cn("flex items-center gap-3 rounded-lg border border-outline-variant bg-surface-container-low p-3 text-sm hover:border-primary", collapsed && "justify-center px-2")} title={currentWorkspace.name}>
              <FolderKanban size={18} />
              {!collapsed ? (
                <span className="min-w-0">
                  <span className="block text-[10px] uppercase tracking-wider text-on-surface-variant">Workspace</span>
                  <strong className="block truncate">{currentWorkspace.name}</strong>
                </span>
              ) : null}
            </Link>
          ) : null}
          <button onClick={signOut} className="flex w-full items-center justify-center gap-3 rounded-lg border border-error/20 bg-error-container/40 p-3 text-left text-sm font-semibold text-error transition hover:bg-error-container">
            <LogOut size={18} />
            {!collapsed ? "Sign out" : null}
          </button>
        </div>
      </aside>
      <main className="min-w-0 pb-28">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-outline-variant bg-surface/80 px-6 backdrop-blur">
          <div className="relative w-full max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" size={18} />
            <input className="w-full rounded-full border border-outline-variant bg-surface-container-low py-2 pl-10 pr-4 text-sm outline-none focus:border-primary" placeholder="Search issues, sprints, or files..." />
          </div>
        </header>
        {children}
      </main>
      {sprintAiWorkspace && !pathname.includes("/sprintflow-ai") ? <SprintAiLauncher workspace={sprintAiWorkspace} /> : null}
      {sessionExpired ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4">
          <div className="w-full max-w-md rounded-xl border border-outline-variant bg-surface p-6 shadow-2xl">
            <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-error-container text-error">
              <AlertTriangle size={22} />
            </div>
            <h2 className="text-2xl font-bold">Sign in again</h2>
            <p className="mt-2 text-on-surface-variant">Your session expired. Please sign in again to continue working.</p>
            <div className="mt-6 flex justify-end">
              <Button onClick={signInAgain}>Go to sign in</Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function SprintAiLauncher({ workspace }: { workspace: Workspace }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");

  function openFullChat() {
    if (draft.trim()) {
      localStorage.setItem("sprintflow_ai_draft", draft.trim());
    }
    router.push(`/workspace/${workspace.id}/sprintflow-ai`);
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 flex h-14 items-center gap-2 rounded-full border border-primary/20 bg-primary px-4 text-sm font-semibold text-white shadow-xl shadow-primary/20 transition hover:bg-primary/90 focus:outline-none focus:ring-4 focus:ring-primary/20"
        aria-label="Open SprintAI chat"
      >
        <Bot size={20} />
        <span>SprintAI</span>
      </button>
    );
  }

  return (
    <section className="fixed bottom-5 right-5 z-40 w-[min(380px,calc(100vw-32px))] rounded-xl border border-outline-variant bg-surface shadow-2xl" aria-label="SprintAI mini chat">
      <header className="flex items-center justify-between gap-3 border-b border-outline-variant p-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary text-white">
            <MessageSquareText size={18} />
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold">SprintAI</h2>
            <p className="truncate text-xs text-on-surface-variant">{workspace.name}</p>
          </div>
        </div>
        <div className="flex gap-1">
          <button onClick={openFullChat} className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container-low" aria-label="Expand SprintAI">
            <ExternalLink size={17} />
          </button>
          <button onClick={() => setOpen(false)} className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container-low" aria-label="Close SprintAI">
            <X size={17} />
          </button>
        </div>
      </header>
      <div className="space-y-3 p-4">
        <div className="rounded-xl bg-surface-container-low p-3 text-sm leading-6 text-on-surface">
          Tell SprintAI what you want to plan. I will open the full workspace chat with your draft ready.
        </div>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          className="min-h-28 w-full resize-none rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-primary"
          placeholder="Example: Build an auth system with admin project access and sprint tasks..."
        />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDraft("")} disabled={!draft.trim()}>Clear</Button>
          <Button onClick={openFullChat}>
            <Send size={16} />
            Open Chat
          </Button>
        </div>
      </div>
    </section>
  );
}
