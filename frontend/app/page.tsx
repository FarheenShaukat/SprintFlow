import Link from "next/link";
import { ArrowRight, BarChart3, Bot, CheckCircle2, Kanban, Users } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <main>
      <header className="flex h-16 items-center justify-between border-b border-outline-variant bg-surface px-6">
        <Link href="/" className="text-xl font-bold text-primary">SprintFlow AI</Link>
        <nav className="hidden items-center gap-6 text-sm text-on-surface-variant md:flex">
          <a>Product</a><a>Solutions</a><a>Pricing</a>
        </nav>
        <div className="flex gap-2">
          <Link href="/login"><Button variant="ghost">Sign In</Button></Link>
          <Link href="/register"><Button>Get Started</Button></Link>
        </div>
      </header>
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <div className="mb-6 inline-flex rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">New: AI sprint health scoring</div>
          <h1 className="text-5xl font-bold leading-tight tracking-tight">Manage software projects with clarity.</h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-on-surface-variant">SprintFlow AI helps teams plan sprints, manage tasks, detect blockers, and turn messy delivery signals into clear next actions.</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/register"><Button className="h-12 px-6">Start Free <ArrowRight size={18} /></Button></Link>
            <Link href="/dashboard"><Button className="h-12 px-6" variant="secondary">View Demo</Button></Link>
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 shadow-soft">
          <div className="mb-4 flex gap-2"><span className="h-3 w-3 rounded-full bg-error/40" /><span className="h-3 w-3 rounded-full bg-amber-400/50" /><span className="h-3 w-3 rounded-full bg-secondary/40" /></div>
          <div className="grid gap-4 md:grid-cols-3">
            {[Kanban, Bot, BarChart3].map((Icon, index) => (
              <div key={index} className="rounded-xl border border-outline-variant bg-surface p-5">
                <Icon className="mb-5 text-primary" />
                <div className="h-3 w-28 rounded bg-surface-variant" />
                <div className="mt-3 h-3 w-20 rounded bg-surface-container-high" />
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-xl border border-outline-variant bg-surface p-5">
            <div className="mb-4 flex items-center gap-3"><Users className="text-secondary" /><strong>Team workload</strong></div>
            <div className="space-y-3">
              {[60, 40, 85].map((value) => <div key={value} className="h-2 rounded-full bg-surface-variant"><div className="h-2 rounded-full bg-primary" style={{ width: `${value}%` }} /></div>)}
            </div>
          </div>
        </div>
      </section>
      <section className="bg-surface-container-low px-6 py-20">
        <div className="mx-auto grid max-w-7xl gap-4 md:grid-cols-3">
          {["Kanban workflows", "AI task insights", "Sprint reports"].map((item) => (
            <div className="rounded-xl border border-outline-variant bg-surface p-6" key={item}>
              <CheckCircle2 className="mb-4 text-primary" />
              <h2 className="text-xl font-semibold">{item}</h2>
              <p className="mt-2 text-sm leading-6 text-on-surface-variant">Built for a realistic SaaS portfolio project with Django REST and Next.js.</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
