"""Incident persistence.

Production: Firestore (Google Cloud's serverless document store — same project,
no extra infra to provision). Local development: an in-memory dict that
behaves identically. The fallback is automatic when no GCP project is
configured, so ``uvicorn app.main:app`` works zero-config out of the box.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.config import Settings
from app.models import Incident

log = structlog.get_logger("triage.store")


class IncidentStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._memory: dict[str, Incident] = {}
        self._client: Any | None = None
        self._use_memory = True

        if settings.google_cloud_project:
            try:
                from google.cloud import firestore

                self._client = firestore.AsyncClient(project=settings.google_cloud_project)
                self._use_memory = False
                log.info(
                    "store.firestore.ready",
                    project=settings.google_cloud_project,
                    collection=settings.firestore_collection_incidents,
                )
            except Exception as exc:
                log.warning("store.firestore.unavailable", error=str(exc))

        if self._use_memory:
            log.info("store.memory_mode.active")

    # --- Public API ---------------------------------------------------------

    async def save(self, incident: Incident) -> None:
        if self._use_memory:
            self._memory[incident.id] = incident.model_copy(deep=True)
            return
        assert self._client is not None
        doc_ref = self._collection().document(incident.id)
        await doc_ref.set(incident.model_dump(mode="json"))

    async def get(self, incident_id: str) -> Incident | None:
        if self._use_memory:
            return self._memory.get(incident_id)
        assert self._client is not None
        snapshot = await self._collection().document(incident_id).get()
        if not snapshot.exists:
            return None
        return Incident.model_validate(snapshot.to_dict())

    async def list_all(self, limit: int = 100) -> list[Incident]:
        if self._use_memory:
            ordered = sorted(
                self._memory.values(),
                key=lambda i: i.detected_at,
                reverse=True,
            )
            return ordered[:limit]
        assert self._client is not None
        # Firestore async streams: collect into a list (small N for now).
        from google.cloud.firestore import Query

        query = (
            self._collection()
            .order_by("detected_at", direction=Query.DESCENDING)
            .limit(limit)
        )
        results: list[Incident] = []
        async for snapshot in query.stream():
            data = snapshot.to_dict()
            if data is not None:
                results.append(Incident.model_validate(data))
        return results

    async def delete_all(self) -> int:
        """Test/demo convenience: wipe the collection (or memory)."""
        if self._use_memory:
            n = len(self._memory)
            self._memory.clear()
            return n
        assert self._client is not None
        count = 0
        async for snapshot in self._collection().stream():
            await snapshot.reference.delete()
            count += 1
        return count

    # --- Internal -----------------------------------------------------------

    def _collection(self) -> Any:
        return self._client.collection(self._settings.firestore_collection_incidents)
