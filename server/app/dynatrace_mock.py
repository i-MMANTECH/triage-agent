"""Mock Dynatrace data for the offline demo.

The bundled scenario simulates a bad deploy of the fictional `shop-checkout`
service that causes the `POST /checkout` endpoint to start returning 500s.
The numbers are deliberately realistic so the agent's reasoning looks credible
on camera.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

# Anchor the timeline relative to "now" so the demo always looks fresh.
NOW = datetime.now(timezone.utc)
PROBLEM_OPENED = NOW - timedelta(minutes=2)
DEPLOY_AT = NOW - timedelta(minutes=3)


MOCK_PROBLEM: dict[str, Any] = {
    "problemId": "PRB-2026-05-13-001",
    "displayId": "P-251301",
    "title": "Failure rate increase on shop-checkout",
    "status": "OPEN",
    "severityLevel": "ERROR",
    "impactLevel": "SERVICE",
    "startTime": PROBLEM_OPENED.isoformat(),
    "affectedEntities": [
        {
            "entityId": "SERVICE-A1B2C3D4E5F6",
            "name": "shop-checkout",
            "type": "SERVICE",
        }
    ],
    "rootCauseEntity": {
        "entityId": "SERVICE-A1B2C3D4E5F6",
        "name": "shop-checkout",
    },
    "managementZones": ["production", "ecommerce"],
    "url": "https://demo.live.dynatrace.com/#problems/problemdetails;pid=PRB-2026-05-13-001",
}


MOCK_ENTITY_DETAIL: dict[str, Any] = {
    "entityId": "SERVICE-A1B2C3D4E5F6",
    "name": "shop-checkout",
    "type": "SERVICE",
    "technologies": ["NODE_JS"],
    "tags": [
        {"key": "env", "value": "production"},
        {"key": "team", "value": "checkout"},
        {"key": "version", "value": "v4.2.0"},
    ],
    "metrics": {
        "failureRate": {
            "baseline": 0.1,
            "current": 18.4,
            "unit": "percent",
        },
        "requestsPerMinute": {
            "current": 2417,
            "unit": "rpm",
        },
        "responseTimeP90Ms": {
            "baseline": 142,
            "current": 187,
            "unit": "ms",
        },
    },
}


MOCK_FAILED_TRACES: list[dict[str, Any]] = [
    {
        "traceId": "7c3f8e2b1a9d4f5e",
        "endpoint": "POST /checkout",
        "statusCode": 500,
        "durationMs": 412,
        "errorMessage": (
            "TypeError: Cannot read properties of undefined (reading 'currency') "
            "at calculateTotals (/app/dist/checkout/totals.js:142:18)"
        ),
        "occurredAt": (PROBLEM_OPENED + timedelta(seconds=30)).isoformat(),
    },
    {
        "traceId": "8d4e9f3c2b0e5a6f",
        "endpoint": "POST /checkout",
        "statusCode": 500,
        "durationMs": 398,
        "errorMessage": (
            "TypeError: Cannot read properties of undefined (reading 'currency') "
            "at calculateTotals (/app/dist/checkout/totals.js:142:18)"
        ),
        "occurredAt": (PROBLEM_OPENED + timedelta(seconds=58)).isoformat(),
    },
    {
        "traceId": "9e5f0a4d3c1f6b7e",
        "endpoint": "POST /checkout",
        "statusCode": 500,
        "durationMs": 405,
        "errorMessage": (
            "TypeError: Cannot read properties of undefined (reading 'currency') "
            "at calculateTotals (/app/dist/checkout/totals.js:142:18)"
        ),
        "occurredAt": (PROBLEM_OPENED + timedelta(seconds=85)).isoformat(),
    },
]


MOCK_DEPLOYMENT_EVENTS: list[dict[str, Any]] = [
    {
        "eventId": "DEPLOY-2026-05-13-shop-checkout-v4.2.0",
        "type": "CUSTOM_DEPLOYMENT",
        "entityId": "SERVICE-A1B2C3D4E5F6",
        "entityName": "shop-checkout",
        "startTime": DEPLOY_AT.isoformat(),
        "endTime": (DEPLOY_AT + timedelta(seconds=45)).isoformat(),
        "properties": {
            "version": "v4.2.0",
            "previousVersion": "v4.1.9",
            "commitSha": "a7f3d92",
            "author": "alice@example.com",
            "changelogUrl": "https://github.com/example/shop/compare/v4.1.9...v4.2.0",
        },
    },
    {
        "eventId": "DEPLOY-2026-05-12-shop-checkout-v4.1.9",
        "type": "CUSTOM_DEPLOYMENT",
        "entityId": "SERVICE-A1B2C3D4E5F6",
        "entityName": "shop-checkout",
        "startTime": (DEPLOY_AT - timedelta(days=1, hours=4)).isoformat(),
        "endTime": (DEPLOY_AT - timedelta(days=1, hours=4) + timedelta(seconds=42)).isoformat(),
        "properties": {
            "version": "v4.1.9",
            "previousVersion": "v4.1.8",
            "commitSha": "c8d4e15",
            "author": "bob@example.com",
        },
    },
]


MOCK_RELATED_PROBLEMS: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Tool implementations — these become Python function tools the LLM can call.
# In production these would be replaced by the live Dynatrace MCP toolset.
# ---------------------------------------------------------------------------


def list_problems() -> dict[str, Any]:
    """List currently open Dynatrace problems.

    Returns:
        A dict with a `problems` list of open problem summaries.
    """
    return {"problems": [MOCK_PROBLEM]}


def get_problem(problem_id: str) -> dict[str, Any]:
    """Get full details for a specific Dynatrace problem.

    Args:
        problem_id: The Dynatrace problem ID (e.g. "PRB-2026-05-13-001").

    Returns:
        The full problem record including affected entities and root-cause entity.
    """
    return MOCK_PROBLEM


def get_entity(entity_id: str) -> dict[str, Any]:
    """Get details about a Dynatrace entity (service, host, process).

    Args:
        entity_id: The Dynatrace entity ID (e.g. "SERVICE-A1B2C3D4E5F6").

    Returns:
        Entity metadata, tags, and current/baseline metrics.
    """
    return MOCK_ENTITY_DETAIL


def get_failed_traces(entity_id: str, since_minutes: int = 5) -> dict[str, Any]:
    """Fetch recent failed request traces for a service entity.

    Args:
        entity_id: The Dynatrace entity ID of the affected service.
        since_minutes: How far back to look. Defaults to 5 minutes.

    Returns:
        A dict with a `traces` list of failed-request samples.
    """
    return {"traces": MOCK_FAILED_TRACES, "entityId": entity_id, "sinceMinutes": since_minutes}


def get_recent_deployments(entity_id: str, since_minutes: int = 60) -> dict[str, Any]:
    """Fetch recent deployment events for an entity.

    Args:
        entity_id: The Dynatrace entity ID of the affected service.
        since_minutes: How far back to look. Defaults to 60 minutes.

    Returns:
        A dict with a `deployments` list ordered most-recent-first.
    """
    return {"deployments": MOCK_DEPLOYMENT_EVENTS, "entityId": entity_id}


def get_related_problems(entity_id: str) -> dict[str, Any]:
    """Find correlated problems on the same or connected entities."""
    return {"relatedProblems": MOCK_RELATED_PROBLEMS, "entityId": entity_id}


def execute_rollback(entity_id: str, target_version: str) -> dict[str, Any]:
    """Roll a service back to a previous version.

    Args:
        entity_id: The Dynatrace entity ID of the service to roll back.
        target_version: The version string to roll back to (e.g. "v4.1.9").

    Returns:
        A dict describing the rollback result.
    """
    return {
        "status": "completed",
        "entityId": entity_id,
        "rolledBackTo": target_version,
        "completedAt": datetime.now(timezone.utc).isoformat(),
    }


def get_service_metrics(entity_id: str) -> dict[str, Any]:
    """Get current service-level metrics — used during the verification phase
    to confirm that an action returned the service to a healthy state.

    Args:
        entity_id: The Dynatrace entity ID of the service to check.

    Returns:
        Current metric values vs baseline.
    """
    # After the rollback, error rate has recovered to baseline.
    return {
        "entityId": entity_id,
        "metrics": {
            "failureRate": {"baseline": 0.1, "current": 0.12, "unit": "percent"},
            "requestsPerMinute": {"current": 2389, "unit": "rpm"},
            "responseTimeP90Ms": {"baseline": 142, "current": 144, "unit": "ms"},
        },
        "healthy": True,
    }


# Convenience: the full list of mock tool functions, in the order an investigator
# is most likely to need them. Used by the agent factory in mock mode.
MOCK_TOOL_FUNCTIONS = [
    list_problems,
    get_problem,
    get_entity,
    get_failed_traces,
    get_recent_deployments,
    get_related_problems,
    get_service_metrics,
]
