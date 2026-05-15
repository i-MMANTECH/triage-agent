"""FastAPI application entrypoint for Triage.

This module wires the lifespan, middleware, and routes. Runtime services
(agent, MCP client, Firestore repo) are constructed once at startup and
attached to ``app.state`` so handlers can pull them from the request.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import IncidentAgent
from app.config import get_settings
from app.logging import configure_logging, get_logger
from app.mcp_client import DynatraceMcpClient
from app.routes import approvals, demo, health, incidents, webhooks
from app.store import IncidentStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("triage.startup")

    # Tell ADK / google-genai which auth path to use. Must run BEFORE the
    # agent is constructed, because the SDK reads these at first import.
    if settings.google_api_key:
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
        log.info("triage.auth.ai_studio")
    elif settings.google_cloud_project:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project
        os.environ["GOOGLE_CLOUD_LOCATION"] = settings.google_cloud_location
        log.info("triage.auth.vertex_ai", project=settings.google_cloud_project)
    else:
        log.warning("triage.auth.missing", msg="No GOOGLE_API_KEY or GCP project set")

    log.info("triage.starting", mock_mode=settings.triage_mock_mode, model=settings.gemini_model)

    store = IncidentStore(settings=settings)
    mcp = DynatraceMcpClient(settings=settings)
    await mcp.start()
    agent = IncidentAgent(settings=settings, mcp=mcp, store=store)

    app.state.settings = settings
    app.state.store = store
    app.state.mcp = mcp
    app.state.agent = agent

    log.info("triage.ready")
    try:
        yield
    finally:
        log.info("triage.shutting_down")
        await mcp.stop()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Triage",
        description="On-call's AI first responder. Built for the Google Cloud Rapid Agent Hackathon.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
    app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
    app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
    app.include_router(demo.router, prefix="/demo", tags=["demo"])

    return app


app = create_app()
