"""Dynatrace problem-notification webhook ingress.

Dynatrace can post problems in slightly varying schemas depending on the
notification template, so we accept a permissive dict and project it through
the lenient :class:`DynatraceProblem` model. Each accepted webhook creates an
Incident, schedules the agent loop in the background, and returns the
incident id immediately — the webhook contract requires a fast 2xx.
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, Request, status

from app.models import (
    DynatraceProblem,
    EventKind,
    Incident,
    IncidentStatus,
    Severity,
)

router = APIRouter()
log = structlog.get_logger("triage.webhooks")


def _map_severity(raw: str) -> Severity:
    raw = (raw or "").upper()
    if raw in {"CRITICAL", "AVAILABILITY"}:
        return Severity.CRITICAL
    if raw in {"ERROR", "PERFORMANCE", "RESOURCE_CONTENTION"}:
        return Severity.ERROR
    if raw in {"WARNING", "MONITORING_UNAVAILABLE", "CUSTOM_ALERT"}:
        return Severity.WARNING
    return Severity.INFO


async def _run_agent_pipeline(request: Request, incident_id: str) -> None:
    """Background task: investigate + propose plan. Approval gate stops here.

    Any exception raised by the agent is captured both to the structured logs
    AND onto the incident timeline so it's visible in the dashboard and the
    ``GET /incidents`` JSON. Without the timeline capture, failures inside the
    background task surface only in stdout where they're easy to miss.
    """
    agent = request.app.state.agent
    store = request.app.state.store
    incident = await store.get(incident_id)
    if incident is None:
        log.warning("webhooks.background.incident_missing", incident_id=incident_id)
        return
    try:
        await agent.investigate_and_plan(incident)
    except Exception as exc:
        log.exception("webhooks.background.failed", incident_id=incident_id)
        incident.status = IncidentStatus.FAILED
        incident.append_event(
            EventKind.ACTION_FAILED,
            f"Agent failed during investigation: {type(exc).__name__}: {exc}",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        try:
            await store.save(incident)
        except Exception:
            log.exception("webhooks.background.store_save_failed", incident_id=incident_id)


@router.post("/dynatrace", status_code=status.HTTP_202_ACCEPTED)
async def receive_dynatrace(
    payload: dict[str, Any],
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    problem = DynatraceProblem.model_validate(payload)

    incident = Incident(
        id=str(uuid4()),
        title=problem.title or "Untitled Dynatrace problem",
        severity=_map_severity(problem.severity),
        dynatrace_problem_id=problem.pid,
        dynatrace_url=problem.url or None,
    )
    incident.append_event(
        EventKind.DETECTED,
        f"Detected via Dynatrace: {incident.title}",
        impact=problem.impact,
        state=problem.state,
    )
    await request.app.state.store.save(incident)
    log.info(
        "webhooks.dynatrace.accepted",
        incident_id=incident.id,
        problem_id=problem.pid,
        title=incident.title,
    )

    # Kick off the agent loop without blocking the webhook caller.
    background_tasks.add_task(_run_agent_pipeline, request, incident.id)

    return {"incident_id": incident.id, "status": incident.status.value}
