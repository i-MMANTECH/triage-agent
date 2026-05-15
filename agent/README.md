# Agent

This directory is intentionally kept as a navigational placeholder. The actual
agent implementation lives inside the backend service to keep the runtime
graph (agent + tools + state + HTTP surface) on a single deployment unit:

- Agent orchestration: [`../server/app/agent.py`](../server/app/agent.py)
- System prompts: [`../server/app/prompts.py`](../server/app/prompts.py)
- Tool / MCP integration: [`../server/app/mcp_client.py`](../server/app/mcp_client.py)
- Structured I/O schemas: [`../server/app/models.py`](../server/app/models.py)

## Design

The agent is a Google ADK `SequentialAgent` with two sub-agents:

1. **investigator** — `LlmAgent` with the Dynatrace MCP toolset bound. Pulls
   problem details, traces, recent deployments, and entity metrics.
2. **planner** — `LlmAgent` with `output_schema=IncidentPlan`. Consumes the
   investigator's findings and produces a structured plan that the dashboard
   renders directly on the approval card.

After human approval, the deterministic executor in
[`server/app/mcp_client.py`](../server/app/mcp_client.py) invokes the
corresponding MCP tool with the approved parameters. No LLM is involved at
execution time — a safety property — so the action that runs is exactly the
one the operator read.
