"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ArrowLeft } from "lucide-react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

const schema = z.object({ fullName: z.string().min(2), email: z.string().email(), password: z.string().min(8) });

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isInvite = Boolean(searchParams.get("next") && searchParams.get("email"));
  const setAccessToken = useAuthStore((state) => state.setAccessToken);
  const { register, handleSubmit, formState: { errors, isSubmitting }, setError } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

  async function onSubmit(values: z.infer<typeof schema>) {
    try {
      const email = values.email.trim().toLowerCase();
      await authApi.register({ full_name: values.fullName.trim(), email, password: values.password });
      const result = await authApi.login({ email, password: values.password });
      localStorage.setItem("sprintflow_refresh", result.refresh);
      setAccessToken(result.access);
      router.push(searchParams.get("next") || "/dashboard");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not create account.";
      setError("root", { message });
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4">
      <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-md rounded-2xl border border-outline-variant bg-surface p-8 shadow-soft">
        <div className="mb-8 flex items-center justify-between gap-4">
          <Link href="/" className="text-xl font-bold text-primary">SprintFlow AI</Link>
          <Link href="/" className="inline-flex items-center gap-2 rounded-lg border border-outline-variant px-3 py-2 text-sm font-medium text-on-surface-variant hover:bg-surface-container-low">
            <ArrowLeft size={16} />
            Back
          </Link>
        </div>
        <h1 className="text-3xl font-bold">{isInvite ? "Create your account" : "Create workspace owner"}</h1>
        <p className="mt-2 text-sm text-on-surface-variant">{isInvite ? "Finish signup to join the invited workspace." : "Start a new software team workspace."}</p>
        <label className="mt-8 block text-sm font-medium">Full name</label>
        <input className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" {...register("fullName")} />
        {errors.fullName ? <p className="mt-1 text-xs text-error">{errors.fullName.message}</p> : null}
        <label className="mt-4 block text-sm font-medium">Email</label>
        <input defaultValue={searchParams.get("email") ?? ""} className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" {...register("email")} />
        {errors.email ? <p className="mt-1 text-xs text-error">{errors.email.message}</p> : null}
        <label className="mt-4 block text-sm font-medium">Password</label>
        <input type="password" className="mt-2 w-full rounded-lg border border-outline-variant px-3 py-2 outline-none focus:border-primary" {...register("password")} />
        {errors.password ? <p className="mt-1 text-xs text-error">{errors.password.message}</p> : null}
        {errors.root ? <p className="mt-4 rounded-lg bg-error-container p-3 text-sm text-error">{errors.root.message}</p> : null}
        <Button className="mt-6 w-full" type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating..." : "Create Account"}</Button>
      </form>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<main className="grid min-h-screen place-items-center px-4">Loading...</main>}>
      <RegisterForm />
    </Suspense>
  );
}
