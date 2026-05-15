"""Cloud Run health probes."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/healthz", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["health"])
async def readiness(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    mcp = request.app.state.mcp
    return {
        "status": "ready",
        "mock_mode": mcp.mock_mode,
        "model": settings.gemini_model,
        "project": settings.google_cloud_project or "unset",
    }
