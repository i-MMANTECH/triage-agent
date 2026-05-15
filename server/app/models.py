"""Pydantic schemas for incidents, plans, actions, and approvals.

These are the contract between the agent (which produces structured output)
and the rest of the system (storage, REST API, dashboard).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Enums --------------------------------------------------------------------


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    FAILED = "failed"


class ActionKind(str, Enum):
    ROLLBACK = "rollback"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART = "restart"
    MUTE_ALERT = "mute_alert"
    FEATURE_FLAG = "feature_flag"
    NOTIFY = "notify"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class EventKind(str, Enum):
    DETECTED = "detected"
    INVESTIGATION_STARTED = "investigation_started"
    INVESTIGATION_FINDING = "investigation_finding"
    PLAN_PROPOSED = "plan_proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
    METRICS_RECOVERED = "metrics_recovered"
    POSTMORTEM_WRITTEN = "postmortem_written"
    RESOLVED = "resolved"


# --- Incoming Dynatrace webhook ----------------------------------------------


class DynatraceProblem(BaseModel):
    """Subset of the Dynatrace problem webhook payload we care about.

    Full schema:
    https://docs.dynatrace.com/docs/observe/problem-detection-and-analysis/problem-notifications
    """

    model_config = ConfigDict(extra="allow")

    pid: str = Field(alias="ProblemID")
    impact: str = Field(default="UNKNOWN", alias="ProblemImpact")
    severity: str = Field(default="UNKNOWN", alias="ProblemSeverity")
    title: str = Field(default="", alias="ProblemTitle")
    detail_html: str = Field(default="", alias="ProblemDetailsHTML")
    detail_text: str = Field(default="", alias="ProblemDetailsText")
    url: str = Field(default="", alias="ProblemURL")
    state: str = Field(default="OPEN", alias="State")
    tags: str = Field(default="", alias="Tags")


# --- Investigation findings ---------------------------------------------------


class Finding(BaseModel):
    """A single piece of evidence the agent gathered during investigation."""

    source: str = Field(description="Which tool produced it (e.g. dynatrace.list_problems)")
    summary: str = Field(description="One-line human-readable summary")
    detail: dict[str, Any] = Field(default_factory=dict, description="Raw payload excerpt")
    at: datetime = Field(default_factory=_utc_now)


# --- Hypotheses + actions (the IncidentPlan) ---------------------------------


class Hypothesis(BaseModel):
    """A candidate root-cause explanation produced by the LLM."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short root-cause label, e.g. 'Bad deploy of shop-checkout v42'")
    rationale: str = Field(description="Why the agent believes this — cite findings by index")
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_finding_indices: list[int] = Field(default_factory=list)


class ActionParameter(BaseModel):
    """One key-value pair in an action's parameter list.

    We use a list-of-pairs rather than ``dict[str, Any]`` because Gemini's
    structured-output schema validator (OpenAPI 3.0 subset) rejects any
    ``additionalProperties`` key — and arbitrary-keyed dicts always produce one.
    """

    model_config = ConfigDict(extra="forbid")
    key: str
    value: str


class Action(BaseModel):
    """A concrete remediation the agent proposes to execute."""

    model_config = ConfigDict(extra="forbid")

    kind: ActionKind
    summary: str = Field(description="Human-readable one-line summary")
    rationale: str = Field(description="Why this action follows from the leading hypothesis")
    target: str = Field(description="What the action operates on (service, deployment, etc.)")
    parameters: list[ActionParameter] = Field(
        default_factory=list,
        description="Tool-call parameters as a list of key-value pairs",
    )
    estimated_risk: Literal["low", "medium", "high"] = Field(default="medium")
    reversible: bool = Field(default=True)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

    def parameters_as_dict(self) -> dict[str, str]:
        """Convenience: collapse the parameter list back into a dict for executors."""
        return {p.key: p.value for p in self.parameters}


class IncidentPlan(BaseModel):
    """Structured output the agent produces from the investigation phase.

    The dashboard renders this directly, and the executor walks the
    `actions` list after a human approves.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(description="One-paragraph plain-English summary of what's wrong")
    blast_radius: str = Field(description="Who/what is affected right now")
    hypotheses: list[Hypothesis] = Field(min_length=1, max_length=5)
    actions: list[Action] = Field(min_length=1, max_length=3)
    requires_human_approval: bool = Field(default=True)


# --- Approval -----------------------------------------------------------------


class ApprovalRequest(BaseModel):
    decision: ApprovalDecision
    edited_action: Action | None = Field(
        default=None,
        description="If decision is EDITED, the operator-modified action to execute instead",
    )
    operator: str = Field(default="unknown", description="Who clicked the button")
    note: str = Field(default="")


# --- Timeline events ----------------------------------------------------------


class IncidentEvent(BaseModel):
    kind: EventKind
    at: datetime = Field(default_factory=_utc_now)
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)


# --- The aggregate root -------------------------------------------------------


class Incident(BaseModel):
    """The full incident record, written to and read from Firestore."""

    id: str
    status: IncidentStatus = IncidentStatus.DETECTED
    severity: Severity = Severity.ERROR
    title: str
    detected_at: datetime = Field(default_factory=_utc_now)
    resolved_at: datetime | None = None
    dynatrace_problem_id: str | None = None
    dynatrace_url: str | None = None
    findings: list[Finding] = Field(default_factory=list)
    plan: IncidentPlan | None = None
    timeline: list[IncidentEvent] = Field(default_factory=list)
    approvals: list[ApprovalRequest] = Field(default_factory=list)
    postmortem: str | None = None

    def append_event(self, kind: EventKind, message: str, **payload: Any) -> IncidentEvent:
        event = IncidentEvent(kind=kind, message=message, payload=payload)
        self.timeline.append(event)
        return event
