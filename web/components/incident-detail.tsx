"use client";

import { ApprovalControls } from "@/components/approval-controls";
import { PlanCard } from "@/components/plan-card";
import { PostmortemView } from "@/components/postmortem-view";
import { StatusBadge } from "@/components/status-badge";
import { Timeline } from "@/components/timeline";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLiveIncident } from "@/components/live-incident";
import type { Incident } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

export function IncidentDetail({ initial }: { initial: Incident }) {
  const incident = useLiveIncident(initial);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
      <div className="space-y-6">
        <header className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={incident.status} />
            <span className="text-xs text-[var(--color-muted-foreground)]">
              Detected {formatRelative(incident.detected_at)}
            </span>
            {incident.dynatrace_problem_id && (
              <span className="font-mono text-xs text-[var(--color-muted-foreground)]">
                {incident.dynatrace_problem_id}
              </span>
            )}
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {incident.title}
          </h1>
        </header>

        {incident.plan ? (
          <PlanCard plan={incident.plan} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Agent is investigating…
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-[var(--color-muted-foreground)]">
              Pulling traces, recent deployments, and entity metrics via the
              Dynatrace MCP server. The plan will appear here as soon as Gemini
              produces it.
            </CardContent>
          </Card>
        )}

        {incident.status === "awaiting_approval" && (
          <ApprovalControls incidentId={incident.id} />
        )}

        {incident.postmortem && (
          <PostmortemView markdown={incident.postmortem} />
        )}
      </div>

      <aside>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            {incident.timeline.length === 0 ? (
              <p className="text-sm text-[var(--color-muted-foreground)]">
                No events yet.
              </p>
            ) : (
              <Timeline events={incident.timeline} />
            )}
          </CardContent>
        </Card>
      </aside>
    </div>
  );
}
