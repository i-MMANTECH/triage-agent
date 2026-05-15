// TypeScript mirrors of the backend Pydantic models. Kept in sync by hand —
// it's a small surface and the safety of typed clients is worth the duplication.

export type Severity = "info" | "warning" | "error" | "critical";

export type IncidentStatus =
  | "detected"
  | "investigating"
  | "awaiting_approval"
  | "executing"
  | "verifying"
  | "resolved"
  | "rejected"
  | "failed";

export type ActionKind =
  | "rollback"
  | "scale_up"
  | "scale_down"
  | "restart"
  | "mute_alert"
  | "feature_flag"
  | "notify";

export type ApprovalDecision = "approved" | "rejected" | "edited";

export type EventKind =
  | "detected"
  | "investigation_started"
  | "investigation_finding"
  | "plan_proposed"
  | "awaiting_approval"
  | "approved"
  | "rejected"
  | "action_started"
  | "action_completed"
  | "action_failed"
  | "metrics_recovered"
  | "postmortem_written"
  | "resolved";

export interface Finding {
  source: string;
  summary: string;
  detail: Record<string, unknown>;
  at: string;
}

export interface Hypothesis {
  title: string;
  rationale: string;
  confidence: number;
  supporting_finding_indices: number[];
}

export interface ActionParameter {
  key: string;
  value: string;
}

export interface Action {
  kind: ActionKind;
  summary: string;
  rationale: string;
  target: string;
  parameters: ActionParameter[];
  estimated_risk: "low" | "medium" | "high";
  reversible: boolean;
  confidence: number;
}

export interface IncidentPlan {
  summary: string;
  blast_radius: string;
  hypotheses: Hypothesis[];
  actions: Action[];
  requires_human_approval: boolean;
}

export interface IncidentEvent {
  kind: EventKind;
  at: string;
  message: string;
  payload: Record<string, unknown>;
}

export interface ApprovalRequest {
  decision: ApprovalDecision;
  edited_action?: Action;
  operator: string;
  note: string;
}

export interface Incident {
  id: string;
  status: IncidentStatus;
  severity: Severity;
  title: string;
  detected_at: string;
  resolved_at: string | null;
  dynatrace_problem_id: string | null;
  dynatrace_url: string | null;
  findings: Finding[];
  plan: IncidentPlan | null;
  timeline: IncidentEvent[];
  approvals: ApprovalRequest[];
  postmortem: string | null;
}
