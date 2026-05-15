# Server

Python FastAPI service that hosts the Dynatrace problem webhook, drives the
ADK agent loop, and brokers human-in-the-loop approvals. Deployed to Cloud
Run.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/webhooks/dynatrace` | Dynatrace problem-notification ingress. Creates an Incident and kicks off the agent in the background. Returns 202 immediately. |
| `GET`  | `/incidents` | List recent incidents (newest first). |
| `GET`  | `/incidents/{id}` | Get a single incident with timeline + plan + postmortem. |
| `GET`  | `/incidents/{id}/stream` | Server-Sent Events stream of incident state changes. |
| `POST` | `/approvals/{incident_id}` | Operator approval/rejection. On approval, triggers deterministic action execution + verification + postmortem. |
| `POST` | `/demo/seed` | Inject the bundled bad-deploy scenario (used during the recorded demo). |
| `POST` | `/demo/reset` | Wipe all incidents — useful between recording takes. |
| `GET`  | `/healthz` | Liveness probe (Cloud Run). |
| `GET`  | `/readyz` | Readiness — exposes current mode + model. |

## Layout

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI entrypoint, lifespan, middleware, route registration |
| `app/config.py` | `pydantic-settings`-based configuration loaded from `.env` |
| `app/logging.py` | `structlog` JSON logging |
| `app/models.py` | Pydantic schemas: Incident, IncidentPlan, Hypothesis, Action, … |
| `app/agent.py` | `IncidentAgent` — ADK SequentialAgent + executor + postmortem |
| `app/prompts.py` | System prompts for investigation, planning, postmortem |
| `app/mcp_client.py` | Dynatrace MCP wrapper (live + offline mock) |
| `app/dynatrace_mock.py` | Bad-deploy fixture data + mock tool functions |
| `app/store.py` | Firestore repository, with in-memory fallback for local dev |
| `app/routes/` | HTTP route modules |
| `Dockerfile` | Multi-stage build (Python 3.13-slim + Node for MCP stdio child) |
| `requirements.txt` | Runtime dependencies |
| `pyproject.toml` | Tooling config (ruff) |

## Run locally

```powershell
cd server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8080
```

Browse the auto-generated API docs at <http://localhost:8080/docs>.
