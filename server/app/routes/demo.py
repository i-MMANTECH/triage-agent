"""Demo helpers — used during the recorded submission video.

A single POST to ``/demo/seed`` injects the bundled ``bad-deploy`` scenario
as a fresh incident and kicks off the agent. This is the button the operator
clicks on camera so the recording is reproducible and doesn't depend on a
live Dynatrace tenant firing a real problem.
"""

from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, Request

from app.dynatrace_mock import MOCK_PROBLEM
from app.models import EventKind, Incident, Severity
from app.routes.webhooks import _run_agent_pipeline

router = APIRouter()
log = structlog.get_logger("triage.demo")


@router.post("/seed")
async def seed_demo_incident(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Create a fresh incident from the bundled bad-deploy scenario."""

    incident = Incident(
        id=str(uuid4()),
        title=MOCK_PROBLEM["title"],
        severity=Severity.ERROR,
        dynatrace_problem_id=MOCK_PROBLEM["problemId"],
        dynatrace_url=MOCK_PROBLEM["url"],
    )
    incident.append_event(
        EventKind.DETECTED,
        f"Detected (demo): {incident.title}",
        scenario="bad-deploy",
    )
    await request.app.state.store.save(incident)
    log.info("demo.seed", incident_id=incident.id)

    background_tasks.add_task(_run_agent_pipeline, request, incident.id)
    return {"incident_id": incident.id, "scenario": "bad-deploy"}


@router.post("/reset")
async def reset_demo(request: Request) -> dict[str, int]:
    """Wipe all incidents — useful between takes when recording the video."""
    deleted = await request.app.state.store.delete_all()
    log.info("demo.reset", deleted=deleted)
    return {"deleted": deleted}
