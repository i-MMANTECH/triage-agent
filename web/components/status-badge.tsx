import { Badge } from "@/components/ui/badge";
import type { IncidentStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const labels: Record<IncidentStatus, string> = {
  detected: "Detected",
  investigating: "Investigating",
  awaiting_approval: "Awaiting approval",
  executing: "Executing",
  verifying: "Verifying",
  resolved: "Resolved",
  rejected: "Rejected",
  failed: "Failed",
};

const variants: Record<IncidentStatus, "info" | "warning" | "success" | "danger" | "default"> = {
  detected: "info",
  investigating: "info",
  awaiting_approval: "warning",
  executing: "info",
  verifying: "info",
  resolved: "success",
  rejected: "default",
  failed: "danger",
};

const liveStatuses: IncidentStatus[] = [
  "detected",
  "investigating",
  "awaiting_approval",
  "executing",
  "verifying",
];

export function StatusBadge({ status }: { status: IncidentStatus }) {
  const live = liveStatuses.includes(status);
  return (
    <Badge variant={variants[status]} className="gap-1.5">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          status === "resolved" && "bg-[var(--color-success)]",
          status === "failed" && "bg-[var(--color-destructive)]",
          status === "rejected" && "bg-[var(--color-muted-foreground)]",
          live && status === "awaiting_approval" && "bg-[var(--color-warning)] pulse-dot",
          live && status !== "awaiting_approval" && "bg-[var(--color-primary)] pulse-dot",
        )}
      />
      {labels[status]}
    </Badge>
  );
}
