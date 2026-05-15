import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import type { Incident } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

export function IncidentList({ incidents }: { incidents: Incident[] }) {
  if (incidents.length === 0) {
    return (
      <Card className="grid place-items-center px-6 py-16 text-center">
        <div className="space-y-2">
          <p className="text-sm font-medium">No incidents yet.</p>
          <p className="text-sm text-[var(--color-muted-foreground)]">
            Click <span className="font-medium">Seed demo incident</span> in the
            header to trigger the bundled bad-deploy scenario.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <ul className="space-y-2">
      {incidents.map((incident) => (
        <li key={incident.id}>
          <Link
            href={`/incidents/${incident.id}`}
            className="group block rounded-lg border bg-[var(--color-card)] p-4 transition-colors hover:bg-[var(--color-muted)]"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <StatusBadge status={incident.status} />
                  <span className="truncate text-sm font-medium">
                    {incident.title}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-[var(--color-muted-foreground)]">
                  <span>Detected {formatRelative(incident.detected_at)}</span>
                  {incident.dynatrace_problem_id && (
                    <>
                      <span>·</span>
                      <span className="font-mono">
                        {incident.dynatrace_problem_id}
                      </span>
                    </>
                  )}
                  {incident.plan?.actions?.[0] && (
                    <>
                      <span>·</span>
                      <span>
                        Proposed: <strong>{incident.plan.actions[0].kind}</strong>
                      </span>
                    </>
                  )}
                </div>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-[var(--color-muted-foreground)] transition-transform group-hover:translate-x-0.5" />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
