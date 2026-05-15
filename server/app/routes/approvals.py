"""Approval endpoint — the human-in-the-loop gate.

When the operator clicks Approve / Reject / Edit on the dashboard, the
frontend posts here. Approval triggers the deterministic action executor
(no LLM in the loop). Rejection ends the incident as ``REJECTED``.
"""

from __future__ import annotations

import asyncio

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.models import (
    ApprovalDecision,
    ApprovalRequest,
    EventKind,
    IncidentStatus,
)

router = APIRouter()
log = structlog.get_logger("triage.approvals")


async def _execute_after_approval(
    request: Request, incident_id: str, action_index: int
) -> None:
    agent = request.app.state.agent
    store = request.app.state.store
    incident = await store.get(incident_id)
    if incident is None or incident.plan is None:
        return
    if action_index < 0 or action_index >= len(incident.plan.actions):
        return
    action = incident.plan.actions[action_index]
    try:
        await agent.execute_action(incident, action)
        await agent.write_postmortem(incident)
    except Exception:
        log.exception("approvals.execute_failed", incident_id=incident_id)


@router.post("/{incident_id}")
async def decide(
    incident_id: str,
    body: ApprovalRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    action_index: int = 0,
) -> dict[str, object]:
    store = request.app.state.store
    incident = await store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if incident.plan is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident has no plan yet — agent is still investigating.",
        )
    if incident.status not in {IncidentStatus.AWAITING_APPROVAL}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Incident is in status {incident.status.value}, cannot accept approval.",
        )

    incident.approvals.append(body)

    if body.decision == ApprovalDecision.REJECTED:
        incident.status = IncidentStatus.REJECTED
        incident.append_event(
            EventKind.REJECTED,
            f"Plan rejected by {body.operator}: {body.note or 'no note'}",
        )
        await store.save(incident)
        return {"status": incident.status.value}

    if body.decision == ApprovalDecision.EDITED and body.edited_action is not None:
        # Replace the targeted action with the operator's edited version.
        incident.plan.actions[action_index] = body.edited_action

    incident.append_event(
        EventKind.APPROVED,
        f"Plan approved by {body.operator}.",
        action_index=action_index,
    )
    await store.save(incident)

    background_tasks.add_task(_execute_after_approval, request, incident_id, action_index)
    return {"status": "executing", "incident_id": incident_id, "action_index": action_index}
