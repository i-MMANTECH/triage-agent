"""Incident read-side API used by the dashboard."""

from __future__ import annotations

import asyncio
import json

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from app.models import Incident

router = APIRouter()
log = structlog.get_logger("triage.incidents")


@router.get("", response_model=list[Incident])
async def list_incidents(request: Request, limit: int = 50) -> list[Incident]:
    return await request.app.state.store.list_all(limit=limit)


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str, request: Request) -> Incident:
    incident = await request.app.state.store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("/{incident_id}/stream")
async def stream_incident(incident_id: str, request: Request) -> EventSourceResponse:
    """Server-Sent Events stream of the incident's current state.

    Naive implementation that polls the store every second — fine for a
    dashboard with a small number of in-flight incidents. A future iteration
    would use a pub/sub channel keyed on the incident id.
    """

    store = request.app.state.store

    async def event_generator():
        previous_payload: str | None = None
        while True:
            if await request.is_disconnected():
                break
            incident = await store.get(incident_id)
            if incident is None:
                yield {"event": "not_found", "data": json.dumps({"incident_id": incident_id})}
                break
            payload = incident.model_dump_json()
            if payload != previous_payload:
                yield {"event": "update", "data": payload}
                previous_payload = payload
                if incident.status.value in {"resolved", "rejected", "failed"}:
                    break
            await asyncio.sleep(1.0)

    return EventSourceResponse(event_generator())
