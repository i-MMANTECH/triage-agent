import {
  AlertTriangle,
  ChevronRight,
  ShieldAlert,
  Sparkles,
  Target,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Action, IncidentPlan } from "@/lib/types";

function riskVariant(risk: Action["estimated_risk"]) {
  if (risk === "high") return "danger" as const;
  if (risk === "medium") return "warning" as const;
  return "success" as const;
}

function confidenceLabel(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function PlanCard({ plan }: { plan: IncidentPlan }) {
  const top = plan.hypotheses[0];
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[var(--color-primary)]" />
          <CardTitle className="text-base">Agent's plan</CardTitle>
        </div>
        <CardDescription>{plan.summary}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-[var(--color-muted-foreground)]">
            <Target className="h-3 w-3" />
            Blast radius
          </div>
          <p className="text-sm">{plan.blast_radius}</p>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-[var(--color-muted-foreground)]">
            <AlertTriangle className="h-3 w-3" />
            Top hypothesis
          </div>
          {top ? (
            <div className="rounded-lg border bg-[var(--color-muted)]/40 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">{top.title}</p>
                <Badge variant="info">{confidenceLabel(top.confidence)}</Badge>
              </div>
              <p className="mt-1.5 text-sm text-[var(--color-muted-foreground)]">
                {top.rationale}
              </p>
            </div>
          ) : (
            <p className="text-sm text-[var(--color-muted-foreground)]">
              No hypothesis produced.
            </p>
          )}
          {plan.hypotheses.length > 1 && (
            <ul className="space-y-1.5 pl-1 text-sm text-[var(--color-muted-foreground)]">
              {plan.hypotheses.slice(1).map((h) => (
                <li key={h.title} className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>
                    <span className="font-medium text-[var(--color-foreground)]">
                      {h.title}
                    </span>
                    <span className="ml-1 text-xs">
                      ({confidenceLabel(h.confidence)})
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-[var(--color-muted-foreground)]">
            <ShieldAlert className="h-3 w-3" />
            Proposed actions
          </div>
          <ol className="space-y-3">
            {plan.actions.map((action, idx) => (
              <li
                key={`${action.kind}-${idx}`}
                className="rounded-lg border bg-[var(--color-card)] p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      <span className="font-mono text-[var(--color-primary)]">
                        {action.kind}
                      </span>{" "}
                      · {action.summary}
                    </p>
                    <p className="text-sm text-[var(--color-muted-foreground)]">
                      {action.rationale}
                    </p>
                    <p className="font-mono text-xs text-[var(--color-muted-foreground)]">
                      target: {action.target}
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <Badge variant={riskVariant(action.estimated_risk)}>
                      {action.estimated_risk} risk
                    </Badge>
                    {action.reversible && (
                      <span className="text-[10px] uppercase tracking-wider text-[var(--color-muted-foreground)]">
                        reversible
                      </span>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </CardContent>
    </Card>
  );
}
