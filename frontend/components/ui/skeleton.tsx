import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-surface-variant/70", className)} />;
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-outline-variant bg-surface p-5">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-5 h-9 w-16" />
      <Skeleton className="mt-3 h-3 w-32" />
    </div>
  );
}

export function RowSkeleton() {
  return (
    <div className="rounded-xl border border-outline-variant bg-surface p-4">
      <Skeleton className="h-4 w-44" />
      <Skeleton className="mt-3 h-3 w-64 max-w-full" />
    </div>
  );
}
