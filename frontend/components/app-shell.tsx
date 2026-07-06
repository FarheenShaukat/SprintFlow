"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertTriangle, BarChart3, Bolt, ChevronsLeft, ChevronsRight, FolderKanban, LayoutDashboard, LogOut, Plus, Search, Settings, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { clearAuthTokens, workspaceApi } from "@/lib/api";
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

  if (!ready) {
    return <main className="grid min-h-screen place-items-center bg-background text-on-surface">Checking session...</main>;
  }

  return (
    <div className={cn("min-h-screen bg-background text-on-surface md:grid", collapsed ? "md:grid-cols-[76px_1fr]" : "md:grid-cols-[260px_1fr]")}>
      <aside className="sticky top-0 hidden h-screen min-h-0 border-r border-outline-variant bg-surface md:flex md:flex-col">
        <div className="shrink-0 flex items-center gap-3 px-4 py-6">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-white">
            <Bolt size={21} />
          </div>
          {!collapsed ? (
            <div className="min-w-0">
              <h1 className="truncate text-xl font-bold leading-none text-primary">SprintFlow AI</h1>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-on-surface-variant">SaaS Platform</p>
            </div>
          ) : null}
          <button onClick={() => setCollapsed((value) => !value)} className="ml-auto rounded-lg p-2 text-on-surface-variant hover:bg-surface-container-low" aria-label="Toggle sidebar">
            {collapsed ? <ChevronsRight size={18} /> : <ChevronsLeft size={18} />}
          </button>
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
        <div className="shrink-0 border-t border-outline-variant bg-surface p-4">
          <button onClick={signOut} className="flex w-full items-center justify-center gap-3 rounded-lg border border-error/20 bg-error-container/40 p-3 text-left text-sm font-semibold text-error transition hover:bg-error-container">
            <LogOut size={18} />
            {!collapsed ? "Sign out" : null}
          </button>
        </div>
      </aside>
      <main className="min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-outline-variant bg-surface/80 px-6 backdrop-blur">
          <div className="relative w-full max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" size={18} />
            <input className="w-full rounded-full border border-outline-variant bg-surface-container-low py-2 pl-10 pr-4 text-sm outline-none focus:border-primary" placeholder="Search issues, sprints, or files..." />
          </div>
        </header>
        {children}
      </main>
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
