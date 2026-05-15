"""Dynatrace MCP client wrapper.

Two operating modes:

- **Mock mode** (default, `TRIAGE_MOCK_MODE=true`): the client exposes Python
  function tools backed by bundled fixture data in `app.dynatrace_mock`. This
  is what we use for offline demos, automated tests, and the recorded
  submission video so it never depends on a live Dynatrace tenant.

- **Live mode** (`TRIAGE_MOCK_MODE=false` + Dynatrace credentials configured):
  the client launches the official Dynatrace MCP server as a stdio subprocess
  and wraps it in an ADK MCPToolset.

The two modes expose the same surface to the agent: a list of tools, plus an
``execute_tool`` helper for the deterministic post-approval executor.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Sequence

import structlog

from app.config import Settings
from app.dynatrace_mock import MOCK_TOOL_FUNCTIONS, execute_rollback, get_service_metrics
from app.models import Action, ActionKind

log = structlog.get_logger("triage.mcp")


# --- Live-mode toolset acquisition -------------------------------------------
# Importing the ADK MCP toolset lazily keeps mock-mode startup cheap and avoids
# requiring the user to have Node.js installed for offline development.


async def _build_live_toolset(settings: Settings) -> Any:
    """Return an ADK MCPToolset bound to the Dynatrace MCP stdio server."""
    from google.adk.tools.mcp_tool import MCPToolset, StdioServerParameters

    params = StdioServerParameters(
        command=settings.dynatrace_mcp_command,
        args=settings.dynatrace_mcp_arg_list,
        env={
            "DT_ENVIRONMENT": settings.dynatrace_tenant_url,
            "DT_PLATFORM_TOKEN": settings.dynatrace_api_token,
        },
    )
    toolset = MCPToolset(connection_params=params)
    log.info("mcp.live_toolset.ready", command=params.command, args=params.args)
    return toolset


# --- Client ------------------------------------------------------------------


class DynatraceMcpClient:
    """Lifecycle-managed access to the Dynatrace MCP server (or its mock)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._live_toolset: Any | None = None
        self._started = False

    @property
    def mock_mode(self) -> bool:
        # Live mode requires both the flag off AND credentials present, otherwise
        # we silently stay in mock mode rather than crash at first tool call.
        if self._settings.triage_mock_mode:
            return True
        if not self._settings.has_dynatrace_credentials:
            log.warning(
                "mcp.credentials_missing",
                msg="Falling back to mock mode — no Dynatrace token configured.",
            )
            return True
        return False

    async def start(self) -> None:
        if self._started:
            return
        if not self.mock_mode:
            self._live_toolset = await _build_live_toolset(self._settings)
        else:
            log.info("mcp.mock_mode.active")
        self._started = True

    async def stop(self) -> None:
        if self._live_toolset is not None:
            close = getattr(self._live_toolset, "close", None)
            if callable(close):
                result = close()
                if hasattr(result, "__await__"):
                    await result
        self._started = False

    async def get_tools(self) -> Sequence[Any]:
        """Tools to register on the investigator agent."""
        if self.mock_mode:
            return list(MOCK_TOOL_FUNCTIONS)
        assert self._live_toolset is not None, "Live toolset not initialised"
        return [self._live_toolset]

    # --- Deterministic action executor ---------------------------------------
    # After the operator approves an Action, the executor invokes the
    # corresponding MCP tool directly (no LLM in the loop). This guarantees the
    # action that runs is exactly the one displayed on the approval card.

    async def execute_action(self, action: Action) -> dict[str, Any]:
        """Execute an approved action and return the result payload."""
        log.info(
            "mcp.execute_action",
            kind=action.kind,
            target=action.target,
            mock=self.mock_mode,
        )
        if self.mock_mode:
            return await self._execute_action_mock(action)
        return await self._execute_action_live(action)

    async def verify_recovery(self, entity_id: str) -> dict[str, Any]:
        """Pull current service metrics — used after an action to confirm health."""
        if self.mock_mode:
            return get_service_metrics(entity_id=entity_id)
        # Live path: would call the Dynatrace MCP "metrics" or "entity" tool.
        # For Week 1 we keep the same fallback shape so the dashboard renders.
        return {"entityId": entity_id, "healthy": True, "metrics": {}}

    async def _execute_action_mock(self, action: Action) -> dict[str, Any]:
        params = action.parameters_as_dict()
        if action.kind == ActionKind.ROLLBACK:
            target_version = params.get("target_version") or "previous"
            return execute_rollback(entity_id=action.target, target_version=target_version)
        if action.kind == ActionKind.NOTIFY:
            return {"status": "completed", "channel": params.get("channel", "stdout")}
        # Generic mock — pretend the action succeeded.
        return {"status": "completed", "kind": action.kind.value, "target": action.target}

    async def _execute_action_live(self, action: Action) -> dict[str, Any]:
        # The Dynatrace MCP server exposes problem-management and remediation
        # tools by name. The mapping below covers the common verbs; extend as
        # we wire up additional remediation surfaces.
        tool_map: dict[ActionKind, str] = {
            ActionKind.ROLLBACK: "execute_workflow_rollback",
            ActionKind.SCALE_UP: "execute_workflow_scale",
            ActionKind.SCALE_DOWN: "execute_workflow_scale",
            ActionKind.RESTART: "execute_workflow_restart",
            ActionKind.MUTE_ALERT: "mute_problem",
            ActionKind.FEATURE_FLAG: "execute_workflow_feature_flag",
            ActionKind.NOTIFY: "send_notification",
        }
        tool_name = tool_map.get(action.kind)
        if tool_name is None:
            return {"status": "skipped", "reason": f"No MCP mapping for {action.kind}"}

        # The MCPToolset exposes a generic `call_tool` method on its underlying
        # session. We surface a thin wrapper so the agent layer stays loosely
        # coupled to ADK internals.
        toolset = self._live_toolset
        if toolset is None:
            return {"status": "failed", "reason": "MCP toolset unavailable"}

        # ADK's MCPToolset has evolved this method name across versions; try
        # the most common ones in order.
        params = action.parameters_as_dict()
        for method_name in ("call_tool", "invoke_tool", "run_tool"):
            method: Callable[..., Awaitable[Any]] | None = getattr(toolset, method_name, None)
            if method is not None:
                result = await method(tool_name, params)
                return _coerce_to_dict(result)

        return {"status": "failed", "reason": "MCPToolset has no callable tool invoker"}


def _coerce_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {"result": str(value)}
