import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const tones = {
  low: "bg-surface-variant text-on-surface-variant",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-error-container text-error",
  success: "bg-emerald-100 text-emerald-700",
  primary: "bg-primary/10 text-primary"
};

export function Badge({ children, tone = "primary", className }: { children: ReactNode; tone?: keyof typeof tones; className?: string }) {
  return <span className={cn("inline-flex rounded-md px-2 py-1 text-[11px] font-bold uppercase", tones[tone], className)}>{children}</span>;
}
