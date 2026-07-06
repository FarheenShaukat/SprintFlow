import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" && "bg-primary text-white hover:bg-primary-container",
        variant === "secondary" && "border border-outline-variant bg-white text-on-surface hover:bg-surface-container-low",
        variant === "ghost" && "text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface",
        variant === "danger" && "bg-error text-white hover:opacity-90",
        className
      )}
      {...props}
    />
  );
}
