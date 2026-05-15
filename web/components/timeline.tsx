import {
  AlertCircle,
  CheckCircle2,
  Cog,
  FileText,
  HelpCircle,
  Search,
  ShieldCheck,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  XCircle,
} from "lucide-react";
import type { IncidentEvent, EventKind } from "@/lib/types";
import { cn, formatTime } from "@/lib/utils";

const icons: Record<EventKind, typeof AlertCircle> = {
  detected: AlertCircle,
  investigation_started: Search,
  investigation_finding: Sparkles,
  plan_proposed: FileText,
  awaiting_approval: HelpCircle,
  approved: ThumbsUp,
  rejected: ThumbsDown,
  action_started: Cog,
  action_completed: CheckCircle2,
  action_failed: XCircle,
  metrics_recovered: ShieldCheck,
  postmortem_written: FileText,
  resolved: CheckCircle2,
};

const colors: Partial<Record<EventKind, string>> = {
  detected: "text-[var(--color-warning)]",
  investigation_finding: "text-[var(--color-primary)]",
  approved: "text-[var(--color-success)]",
  rejected: "text-[var(--color-muted-foreground)]",
  action_completed: "text-[var(--color-success)]",
  action_failed: "text-[var(--color-destructive)]",
  metrics_recovered: "text-[var(--color-success)]",
  resolved: "text-[var(--color-success)]",
};

export function Timeline({ events }: { events: IncidentEvent[] }) {
  return (
    <ol className="space-y-3">
      {events.map((event, idx) => {
        const Icon = icons[event.kind] ?? AlertCircle;
        return (
          <li
            key={`${event.kind}-${event.at}-${idx}`}
            className="flex gap-3"
          >
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "grid h-7 w-7 place-items-center rounded-full bg-[var(--color-muted)] ring-1 ring-[var(--color-border)]",
                  colors[event.kind] ?? "text-[var(--color-foreground)]",
                )}
              >
                <Icon className="h-3.5 w-3.5" />
              </div>
              {idx < events.length - 1 && (
                <div className="mt-1 h-full w-px flex-1 bg-[var(--color-border)]" />
              )}
            </div>
            <div className="min-w-0 flex-1 pb-3">
              <p className="break-words text-sm leading-snug">{event.message}</p>
              <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
                {formatTime(event.at)}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
