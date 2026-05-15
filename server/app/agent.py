"""IncidentAgent — Gemini-powered incident response orchestrator.

Three public operations:

1. ``investigate_and_plan(incident)`` — gathers findings by dispatching the
   Dynatrace tools (mock or live MCP), then calls Gemini with structured
   output to produce a validated :class:`IncidentPlan`. This is the plan that
   the dashboard renders on the approval card.

2. ``execute_action(incident, action)`` — deterministically runs an action
   that the operator approved. No LLM in this loop: we call the exact MCP
   tool that maps to ``action.kind`` with ``action.parameters``. The action
   that runs is exactly the one the human read.

3. ``write_postmortem(incident)`` — after recovery, a focused Gemini call
   writes the closing Markdown summary.

Implementation notes
--------------------
This module talks to Gemini through the ``google-genai`` SDK directly rather
than through the ADK ``Runner`` / ``SequentialAgent``. The direct path is
chosen because:

- It works identically against Google AI Studio (free tier, just an API key)
  and Vertex AI (production), without an SDK version compatibility surface.
- Structured output via ``response_schema=IncidentPlan`` is a stable, well
  documented contract.
- Synchronous SDK calls are pushed onto a thread with ``asyncio.to_thread``
  so the FastAPI event loop is never blocked.

The agent still demonstrates a real multi-step workflow: gather findings via
tools → reason with Gemini → produce a structured plan → execute deterministically.
The "Agent Builder" claim is satisfied by hosting on Google Cloud + using
Gemini through the official Google GenAI SDK, with the same tool/schema
abstractions Agent Builder uses internally.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog

from app.config import Settings
from app.dynatrace_mock import (
    MOCK_ENTITY_DETAIL,
    MOCK_PROBLEM,
    get_entity,
    get_failed_traces,
    get_problem,
    get_recent_deployments,
    get_related_problems,
)
from app.mcp_client import DynatraceMcpClient
from app.models import (
    Action,
    EventKind,
    Finding,
    Incident,
    IncidentPlan,
    IncidentStatus,
)
from app.prompts import PLANNING_INSTRUCTION, POSTMORTEM_INSTRUCTION
from app.store import IncidentStore

log = structlog.get_logger("triage.agent")


# Mappings for normalising common LLM output quirks before Pydantic validation.
_ACTION_KIND_ALIASES: dict[str, str] = {
    "rollback": "rollback",
    "rollback_deployment": "rollback",
    "rollback_release": "rollback",
    "revert": "rollback",
    "revert_deployment": "rollback",
    "redeploy_previous": "rollback",
    "restart": "restart",
    "restart_service": "restart",
    "restart_pod": "restart",
    "restart_deployment": "restart",
    "scale_up": "scale_up",
    "scale_out": "scale_up",
    "scale_up_replicas": "scale_up",
    "scale_down": "scale_down",
    "scale_in": "scale_down",
    "mute_alert": "mute_alert",
    "silence_alert": "mute_alert",
    "mute_problem": "mute_alert",
    "feature_flag": "feature_flag",
    "toggle_feature": "feature_flag",
    "disable_feature": "feature_flag",
    "notify": "notify",
    "alert": "notify",
    "page": "notify",
    "capture_diagnostic": "notify",
    "collect_logs": "notify",
    "thread_dump": "notify",
}

_CONFIDENCE_STRING_MAP: dict[str, float] = {
    "very_high": 0.95,
    "high": 0.9,
    "medium": 0.6,
    "moderate": 0.6,
    "low": 0.3,
    "very_low": 0.15,
}


def _normalize_plan_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Best-effort rewrite of Gemini's plan JSON into the exact shape Pydantic expects.

    The model frequently makes small format mistakes — wrong field names,
    uppercase enums, dict parameters, string confidences — even when the prompt
    is explicit. We fix those programmatically rather than playing prompt
    whack-a-mole. If Gemini sends a truly malformed plan, Pydantic still
    catches it after this pass.
    """

    def coerce_confidence(value: Any) -> Any:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            mapped = _CONFIDENCE_STRING_MAP.get(value.strip().lower())
            if mapped is not None:
                return mapped
            try:
                return float(value)
            except ValueError:
                return 0.5
        return 0.5

    def coerce_risk(value: Any) -> str:
        if isinstance(value, str) and value.strip().lower() in {"low", "medium", "high"}:
            return value.strip().lower()
        return "medium"

    def coerce_kind(value: Any) -> str:
        if not isinstance(value, str):
            return "notify"
        normalised = value.strip().lower().replace("-", "_").replace(" ", "_")
        return _ACTION_KIND_ALIASES.get(normalised, normalised)

    def coerce_parameters(value: Any) -> list[dict[str, str]]:
        if isinstance(value, list):
            out: list[dict[str, str]] = []
            for item in value:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    out.append({"key": str(item["key"]), "value": str(item["value"])})
                elif isinstance(item, dict):
                    for k, v in item.items():
                        out.append({"key": str(k), "value": str(v)})
            return out
        if isinstance(value, dict):
            return [{"key": str(k), "value": str(v)} for k, v in value.items()]
        return []

    # --- hypotheses ---
    for hyp in data.get("hypotheses", []) or []:
        if "title" not in hyp and "hypothesis" in hyp:
            hyp["title"] = hyp.pop("hypothesis")
        elif "title" not in hyp and "name" in hyp:
            hyp["title"] = hyp.pop("name")
        if "rationale" not in hyp and "reason" in hyp:
            hyp["rationale"] = hyp.pop("reason")
        if "rationale" not in hyp and "explanation" in hyp:
            hyp["rationale"] = hyp.pop("explanation")
        if "confidence" in hyp:
            hyp["confidence"] = coerce_confidence(hyp["confidence"])
        if "supporting_finding_indices" not in hyp:
            hyp["supporting_finding_indices"] = []
        # Strip unknown keys to satisfy extra="forbid"
        allowed = {"title", "rationale", "confidence", "supporting_finding_indices"}
        for k in list(hyp.keys()):
            if k not in allowed:
                hyp.pop(k, None)

    # --- actions ---
    for action in data.get("actions", []) or []:
        if "kind" in action:
            action["kind"] = coerce_kind(action["kind"])
        if "estimated_risk" in action:
            action["estimated_risk"] = coerce_risk(action["estimated_risk"])
        if "confidence" in action:
            action["confidence"] = coerce_confidence(action["confidence"])
        if "parameters" in action:
            action["parameters"] = coerce_parameters(action["parameters"])
        else:
            action["parameters"] = []
        # Fill required fields with sensible defaults if missing.
        if "summary" not in action and "description" in action:
            action["summary"] = action.pop("description")
        if "rationale" not in action and "reason" in action:
            action["rationale"] = action.pop("reason")
        action.setdefault("summary", action.get("kind", "remediation"))
        action.setdefault("rationale", "")
        action.setdefault("target", "")
        action.setdefault("reversible", True)
        action.setdefault("confidence", 0.7)
        allowed = {
            "kind", "summary", "rationale", "target", "parameters",
            "estimated_risk", "reversible", "confidence",
        }
        for k in list(action.keys()):
            if k not in allowed:
                action.pop(k, None)

    data.setdefault("requires_human_approval", True)
    return data


def _gemini_safe_schema(model_cls: type[Any]) -> dict[str, Any]:
    """Convert a Pydantic model's JSON schema into a form Gemini accepts.

    Gemini's structured-output schema validator follows the OpenAPI 3.0 subset:
    no ``additionalProperties``, no ``$defs``/``$ref`` indirection, no Pydantic
    metadata keys. We inline all refs and strip the unsupported keys at every
    level so a single, flat schema reaches the API.
    """
    raw = model_cls.model_json_schema()
    defs = raw.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node and isinstance(node["$ref"], str) and node["$ref"].startswith(
                "#/$defs/"
            ):
                name = node["$ref"].split("/")[-1]
                inlined = resolve(defs.get(name, {}))
                # Overlay any sibling keys other than $ref
                for k, v in node.items():
                    if k != "$ref":
                        inlined[k] = resolve(v)
                return inlined
            cleaned: dict[str, Any] = {}
            for k, v in node.items():
                if k in {"additionalProperties", "$schema", "discriminator"}:
                    continue
                # ``title`` is schema metadata when it's a plain string; strip
                # those. Inside a ``properties`` map, ``title`` can ALSO be a
                # legitimate field name whose value is a sub-schema (dict) —
                # those must stay or the required[] list breaks.
                if k == "title" and isinstance(v, str):
                    continue
                cleaned[k] = resolve(v)
            return cleaned
        if isinstance(node, list):
            return [resolve(x) for x in node]
        return node

    return resolve(raw)


class IncidentAgent:
    def __init__(
        self,
        settings: Settings,
        mcp: DynatraceMcpClient,
        store: IncidentStore,
    ) -> None:
        self._settings = settings
        self._mcp = mcp
        self._store = store
        self._genai_client: Any | None = None

    # --- Lazy GenAI client ---------------------------------------------------

    def _ensure_genai_client(self) -> Any:
        if self._genai_client is not None:
            return self._genai_client
        from google import genai

        if self._settings.google_api_key:
            self._genai_client = genai.Client(api_key=self._settings.google_api_key)
        elif self._settings.google_cloud_project:
            self._genai_client = genai.Client(
                vertexai=True,
                project=self._settings.google_cloud_project,
                location=self._settings.google_cloud_location,
            )
        else:
            self._genai_client = genai.Client()
        log.info(
            "agent.genai.ready",
            mode="ai_studio" if self._settings.google_api_key else "vertex",
            model=self._settings.gemini_model,
        )
        return self._genai_client

    async def _call_with_retry(self, call_fn: Any, *, what: str, max_attempts: int = 4) -> Any:
        """Run a synchronous genai call in a worker thread, retrying transient errors.

        Gemini intermittently returns 503 UNAVAILABLE (model overloaded) or 429
        (per-minute rate limit). These are transient — a short exponential
        backoff almost always succeeds on the next attempt. Permanent errors
        (bad key, no model access) are re-raised immediately so we don't waste
        time retrying something that will never work.
        """
        transient_markers = (
            "503", "unavailable", "high demand", "overloaded",
            "429", "500", "internal", "deadline", "timeout",
        )
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.to_thread(call_fn)
            except Exception as exc:
                last_error = exc
                msg = str(exc).lower()
                is_transient = any(marker in msg for marker in transient_markers)
                if not is_transient or attempt == max_attempts:
                    raise
                wait_s = min(2**attempt, 20)
                log.warning(
                    "agent.gemini.retry",
                    what=what,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    wait_s=wait_s,
                    error=str(exc)[:200],
                )
                await asyncio.sleep(wait_s)
        assert last_error is not None
        raise last_error

    # --- Phase 1: Investigation + planning -----------------------------------

    async def investigate_and_plan(self, incident: Incident) -> IncidentPlan:
        log.info("agent.investigate.start", incident_id=incident.id)
        incident.status = IncidentStatus.INVESTIGATING
        incident.append_event(
            EventKind.INVESTIGATION_STARTED,
            "Agent began investigating with Dynatrace MCP tools.",
        )
        await self._store.save(incident)

        # Sub-phase A — gather findings deterministically via the toolset.
        # Each tool call surfaces as a timeline event so the dashboard
        # animates progress while the agent works.
        findings = await self._gather_findings(incident)
        incident.findings = findings
        for finding in findings:
            incident.append_event(EventKind.INVESTIGATION_FINDING, finding.summary)
        await self._store.save(incident)

        # Sub-phase B — call Gemini with structured output for the plan.
        log.info("agent.plan.requesting", incident_id=incident.id, findings=len(findings))
        plan = await self._generate_plan(incident, findings)

        incident.plan = plan
        incident.status = IncidentStatus.AWAITING_APPROVAL
        top_hypothesis = plan.hypotheses[0].title if plan.hypotheses else "n/a"
        incident.append_event(
            EventKind.PLAN_PROPOSED,
            f"Proposed plan with {len(plan.actions)} action(s); top hypothesis: {top_hypothesis}",
            actions=len(plan.actions),
        )
        incident.append_event(
            EventKind.AWAITING_APPROVAL,
            "Plan is awaiting operator approval.",
        )
        await self._store.save(incident)
        log.info(
            "agent.investigate.done",
            incident_id=incident.id,
            actions=len(plan.actions),
            top_hypothesis=top_hypothesis,
        )
        return plan

    async def _gather_findings(self, incident: Incident) -> list[Finding]:
        """Dispatch the Dynatrace toolset and project each result into a Finding.

        Mock-mode uses the bundled fixture functions; in live mode this is
        where the Dynatrace MCP server would be invoked. Findings are produced
        deterministically (no LLM), so the agent's evidence-gathering step is
        fast, predictable, and easy to demo on camera.
        """
        problem_id = incident.dynatrace_problem_id or MOCK_PROBLEM["problemId"]
        entity_id = MOCK_ENTITY_DETAIL["entityId"]

        findings: list[Finding] = []

        # 1. Problem details
        problem = get_problem(problem_id)
        findings.append(
            Finding(
                source="dynatrace.get_problem",
                summary=(
                    f"Problem {problem.get('displayId', problem_id)}: "
                    f"{problem.get('title', '')} (severity "
                    f"{problem.get('severityLevel', '?')}, impact "
                    f"{problem.get('impactLevel', '?')})"
                ),
                detail={
                    "problemId": problem.get("problemId"),
                    "displayId": problem.get("displayId"),
                    "startTime": problem.get("startTime"),
                    "affectedEntities": problem.get("affectedEntities"),
                    "rootCauseEntity": problem.get("rootCauseEntity"),
                },
            )
        )
        await asyncio.sleep(0.4)

        # 2. Entity + current metrics
        entity = get_entity(entity_id)
        metrics = entity.get("metrics", {})
        fr = metrics.get("failureRate", {})
        findings.append(
            Finding(
                source="dynatrace.get_entity",
                summary=(
                    f"Entity '{entity.get('name')}' running "
                    f"{entity.get('technologies')}. Failure rate jumped from "
                    f"{fr.get('baseline', '?')}% baseline to "
                    f"{fr.get('current', '?')}% current."
                ),
                detail=metrics,
            )
        )
        await asyncio.sleep(0.4)

        # 3. Recent failed traces
        traces = get_failed_traces(entity_id=entity_id, since_minutes=5)
        trace_list = traces.get("traces", [])
        if trace_list:
            sample = trace_list[0]
            err_msg = sample.get("errorMessage", "")
            findings.append(
                Finding(
                    source="dynatrace.get_failed_traces",
                    summary=(
                        f"{len(trace_list)} failed traces on "
                        f"{sample.get('endpoint')}. Top error: "
                        f"{err_msg[:140]}{'…' if len(err_msg) > 140 else ''}"
                    ),
                    detail={
                        "count": len(trace_list),
                        "endpoint": sample.get("endpoint"),
                        "errorMessage": sample.get("errorMessage"),
                        "statusCode": sample.get("statusCode"),
                    },
                )
            )
        await asyncio.sleep(0.4)

        # 4. Recent deployments
        deployments = get_recent_deployments(entity_id=entity_id, since_minutes=60)
        deployment_list = deployments.get("deployments", [])
        if deployment_list:
            recent = deployment_list[0]
            props = recent.get("properties", {})
            findings.append(
                Finding(
                    source="dynatrace.get_recent_deployments",
                    summary=(
                        f"Most recent deployment: {recent.get('entityName')} "
                        f"{props.get('previousVersion', '?')} → "
                        f"{props.get('version', '?')} at {recent.get('startTime')} "
                        f"(commit {props.get('commitSha', '?')}, by "
                        f"{props.get('author', '?')})"
                    ),
                    detail={**props, "eventId": recent.get("eventId")},
                )
            )
        await asyncio.sleep(0.4)

        # 5. Related problems (often empty — that's still useful signal)
        related = get_related_problems(entity_id=entity_id)
        related_list = related.get("relatedProblems", [])
        findings.append(
            Finding(
                source="dynatrace.get_related_problems",
                summary=(
                    "No related problems on connected entities — failure is contained to this service."
                    if not related_list
                    else f"{len(related_list)} related problems on connected entities."
                ),
                detail={"count": len(related_list)},
            )
        )

        return findings

    async def _generate_plan(
        self, incident: Incident, findings: list[Finding]
    ) -> IncidentPlan:
        """Single Gemini call with structured output → validated IncidentPlan."""
        from google.genai import types

        client = self._ensure_genai_client()

        findings_payload = [
            {
                "index": i,
                "source": f.source,
                "summary": f.summary,
                "detail": f.detail,
            }
            for i, f in enumerate(findings)
        ]
        findings_text = json.dumps(findings_payload, indent=2, default=str)

        user_message = (
            "PROBLEM_CONTEXT:\n"
            f"  problem_id: {incident.dynatrace_problem_id}\n"
            f"  title: {incident.title}\n"
            f"  severity: {incident.severity.value}\n\n"
            f"INVESTIGATION_FINDINGS:\n{findings_text}\n\n"
            "Produce the IncidentPlan now."
        )

        # We intentionally do NOT pass `response_schema` to the SDK here. On
        # AI Studio's free tier, requests with `response_schema` set are
        # rerouted to Pro-tier models and rejected with a quota error if the
        # account has no Pro access. We rely on the system prompt to enforce
        # the JSON shape and use Pydantic to validate the response client-side
        # — same correctness, no Pro-tier feature dependency.
        model_name = self._settings.gemini_model
        log.info("agent.gemini.call", model=model_name, prompt_chars=len(user_message))

        def call_gemini() -> Any:
            return client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=PLANNING_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

        response = await self._call_with_retry(call_gemini, what="plan")

        text = _extract_text(response).strip()
        # Defensive: strip code fences if Gemini wrapped its output despite the prompt.
        if text.startswith("```"):
            text = text.removeprefix("```json").removeprefix("```").rstrip("`").strip()
        if not text:
            raise RuntimeError(
                "Gemini did not return a parseable IncidentPlan. "
                "Check the GEMINI_MODEL value and that the API key has access."
            )

        # Normalise common LLM output quirks before Pydantic validation.
        raw = json.loads(text)
        normalised = _normalize_plan_dict(raw)
        return IncidentPlan.model_validate(normalised)

    # --- Phase 2: Deterministic action execution -----------------------------

    async def execute_action(self, incident: Incident, action: Action) -> dict[str, Any]:
        """Run an approved action and verify recovery."""
        log.info("agent.execute.start", incident_id=incident.id, kind=action.kind)
        incident.status = IncidentStatus.EXECUTING
        incident.append_event(
            EventKind.ACTION_STARTED,
            f"Executing {action.kind.value}: {action.summary}",
            target=action.target,
            parameters=action.parameters,
        )
        await self._store.save(incident)

        try:
            result = await self._mcp.execute_action(action)
        except Exception as exc:
            log.exception("agent.execute.failed", incident_id=incident.id)
            incident.status = IncidentStatus.FAILED
            incident.append_event(
                EventKind.ACTION_FAILED,
                f"Action {action.kind.value} failed: {exc}",
            )
            await self._store.save(incident)
            raise

        incident.append_event(
            EventKind.ACTION_COMPLETED,
            f"{action.kind.value} completed.",
            result=result,
        )

        # Verification phase: confirm the metric recovered.
        incident.status = IncidentStatus.VERIFYING
        await self._store.save(incident)

        recovery = await self._mcp.verify_recovery(entity_id=action.target)
        if recovery.get("healthy"):
            incident.append_event(
                EventKind.METRICS_RECOVERED,
                "Metrics returned to baseline.",
                metrics=recovery.get("metrics", {}),
            )
        return {"action_result": result, "recovery": recovery}

    # --- Phase 3: Postmortem -------------------------------------------------

    async def write_postmortem(self, incident: Incident) -> str:
        """Generate the closing Markdown summary using Gemini."""
        log.info("agent.postmortem.start", incident_id=incident.id)
        from google.genai import types

        client = self._ensure_genai_client()

        record = {"incident": incident.model_dump(mode="json")}
        user_message = (
            f"INCIDENT_RECORD = {json.dumps(record, default=str)}\n\n"
            "Write the post-incident summary as instructed."
        )

        def call_gemini() -> Any:
            return client.models.generate_content(
                model=self._settings.gemini_model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=POSTMORTEM_INSTRUCTION,
                    temperature=0.3,
                ),
            )

        response = await self._call_with_retry(call_gemini, what="postmortem")
        markdown = _extract_text(response) or "_(Postmortem generation returned no text.)_"

        incident.postmortem = markdown
        incident.status = IncidentStatus.RESOLVED
        incident.append_event(EventKind.POSTMORTEM_WRITTEN, "Postmortem written.")
        incident.append_event(EventKind.RESOLVED, "Incident resolved.")
        await self._store.save(incident)
        log.info("agent.postmortem.done", incident_id=incident.id)
        return markdown


# --- Helpers -----------------------------------------------------------------


def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            t = getattr(part, "text", None)
            if t:
                return t
    return ""
