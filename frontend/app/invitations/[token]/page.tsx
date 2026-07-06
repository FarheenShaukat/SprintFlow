"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { invitationApi, type InvitationAccept } from "@/lib/api";

export default function InvitationAcceptPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const token = params.token;
  const [result, setResult] = useState<InvitationAccept | null>(null);
  const [seconds, setSeconds] = useState(15);
  const [error, setError] = useState("");

  const nextUrl = useMemo(() => result ? `/workspace/${result.workspace_id}` : "/dashboard", [result]);
  const authUrl = useMemo(() => {
    if (!result) return "/login";
    const params = new URLSearchParams({ next: nextUrl });
    if (!result.user_exists) params.set("email", result.email);
    return `${result.user_exists ? "/login" : "/register"}?${params.toString()}`;
  }, [nextUrl, result]);

  useEffect(() => {
    async function accept() {
      try {
        const accepted = await invitationApi.accept(token);
        setResult(accepted);
      } catch {
        setError("This invitation is invalid or has already been removed.");
      }
    }
    void accept();
  }, [token]);

  useEffect(() => {
    if (!result) return;
    const interval = window.setInterval(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    const timeout = window.setTimeout(() => router.push(authUrl), 15000);
    return () => {
      window.clearInterval(interval);
      window.clearTimeout(timeout);
    };
  }, [authUrl, result, router]);

  return (
    <main className="grid min-h-screen place-items-center bg-background px-4">
      <section className="w-full max-w-xl rounded-2xl border border-outline-variant bg-surface p-8 text-center shadow-soft">
        {error ? (
          <>
            <h1 className="text-3xl font-bold text-error">Invitation problem</h1>
            <p className="mt-3 text-on-surface-variant">{error}</p>
            <Link href="/"><Button className="mt-6">Back to Home</Button></Link>
          </>
        ) : !result ? (
          <>
            <Loader2 className="mx-auto animate-spin text-primary" size={40} />
            <h1 className="mt-5 text-3xl font-bold">Accepting invitation...</h1>
          </>
        ) : (
          <>
            <CheckCircle2 className="mx-auto text-emerald-600" size={48} />
            <h1 className="mt-5 text-3xl font-bold">Invitation accepted</h1>
            <p className="mt-3 text-on-surface-variant">
              You accepted the invite to <strong>{result.workspace_name}</strong>.
            </p>
            <div className="mt-6 rounded-xl bg-surface-container-low p-4 text-sm text-on-surface-variant">
              {result.user_exists ? "Sign in to open the workspace." : "Create your account with the invited email to open the workspace."}
              <br />
              Redirecting in {seconds} seconds.
            </div>
            <Link href={authUrl}><Button className="mt-6">{result.user_exists ? "Sign In Now" : "Sign Up Now"}</Button></Link>
          </>
        )}
      </section>
    </main>
  );
}
