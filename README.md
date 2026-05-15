# Triage

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Built with Gemini](https://img.shields.io/badge/Built%20with-Gemini-4285F4)](https://cloud.google.com/products/gemini)
[![Google Cloud Agent Builder](https://img.shields.io/badge/Google%20Cloud-Agent%20Builder-4285F4)](https://cloud.google.com/products/agent-builder)
[![Dynatrace MCP](https://img.shields.io/badge/MCP-Dynatrace-1496FF)](https://www.dynatrace.com/)

> AI that doesn't just answer alerts — it triages them.

**Submitted to:** [Google Cloud Rapid Agent Hackathon](https://rapid-agent.devpost.com/) — **Dynatrace track**

Triage is an autonomous on-call SRE agent that watches your Dynatrace tenant,
diagnoses production incidents the moment they fire, proposes ranked
remediations, and — with one human approval — executes the fix and confirms
recovery.

| Link | URL |
|---|---|
| **Live demo** | **<https://triage-web-407454021889.us-central1.run.app>** |
| Demo video (3 min) | <https://youtu.be/d-9pDGW1zUs> |
| Backend API | <https://triage-server-407454021889.us-central1.run.app> |
| Devpost submission | _added on final Submit_ |
| Demo scenario script | [`demo/scenarios/bad-deploy.md`](demo/scenarios/bad-deploy.md) |

> Open the live demo and click **Seed demo incident** in the header. The agent runs the full bundled scenario against Gemini on Vertex AI in ~20 seconds — no Dynatrace tenant required.

## The problem

Every production incident starts the same way: someone gets paged at 2am,
opens their laptop, and spends the first ten minutes doing the same
mechanical work — reading the alert, pulling traces, checking recent
deployments, forming a hypothesis, deciding what to try first. That work is
high-stakes but low-creativity. **It's exactly what an agent should do.**

## How it works

```
Dynatrace problem ──▶ Cloud Run webhook ──▶ Agent Builder (ADK)
                                                │
                                ┌───────────────┼───────────────┐
                                ▼               ▼               ▼
                       Dynatrace MCP      Gemini 3 reasoning   Firestore
                       (problems,         (hypotheses,         (incident
                        traces, logs,      action plans,        timeline,
                        events, actions)   postmortems)         approvals)
                                                │
                                                ▼
                                  Next.js dashboard (Cloud Run)
                                  — human-in-the-loop approvals
```

1. **Listen** — Dynatrace fires a problem; a webhook hits `POST /webhooks/dynatrace`.
2. **Investigate** — An ADK `SequentialAgent` calls Dynatrace MCP tools to pull
   the problem context, affected entities, recent traces, and change events.
3. **Reason** — Gemini 3 forms ranked hypotheses with confidence scores.
4. **Plan** — A second LLM phase produces a structured `IncidentPlan` (Pydantic
   schema, validated client-side) with 1–3 ranked actions.
5. **Approve** — Plan is rendered on a Next.js dashboard. Operator clicks Approve.
6. **Act** — A deterministic executor runs the approved action via Dynatrace MCP.
   No LLM in this loop — the action that runs is exactly the one displayed.
7. **Verify** — Triage polls metrics until recovery is confirmed.
8. **Postmortem** — Gemini writes the closing summary; the incident closes.

## Tech stack

| Layer | Choice |
|---|---|
| Agent runtime | Google **Agent Development Kit (ADK)** — `SequentialAgent(investigator, planner)` |
| LLM | **Gemini 3** via Vertex AI |
| Partner integration | **Dynatrace MCP server** (stdio) |
| Backend | Python 3.13, FastAPI, deployed on **Cloud Run** |
| Frontend | Next.js 16 (App Router), Tailwind 4, shadcn-style primitives, on Cloud Run |
| State | **Firestore** (in-memory fallback for local dev) |
| Auth | Firebase Auth-ready (not enforced in v0.1) |
| License | Apache 2.0 |

Everything runs on Google Cloud — no competing-cloud dependencies, complying
with the hackathon's track rules.

## Quickstart — run locally in five minutes

Triage ships in **mock mode** by default: it uses bundled Dynatrace fixture
data and runs without a GCP project or Dynatrace tenant. This is also the mode
we record the submission video in.

```powershell
# 1. Backend
cd server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8080
```

```powershell
# 2. Frontend (new terminal)
cd web
npm install
copy .env.example .env.local
npm run dev
```

Open <http://localhost:3000> and click **Seed demo incident** in the header.
The agent runs the full pipeline against the bundled bad-deploy scenario.

> **Note on Gemini model availability:** mock mode skips real Gemini calls for
> the deterministic action executor, but the agent's investigation + planning
> phases still call the model. If `gemini-3.0-pro` is not yet available in
> your project, set `GEMINI_MODEL` in `server/.env` to whichever model your
> project has access to (e.g. `gemini-2.5-pro`).

## Deploy to Cloud Run

```powershell
# 1. One-time GCP setup (enables APIs, creates Firestore + service account)
./scripts/bootstrap.ps1 -ProjectId <your-gcp-project-id>

# 2. Deploy the FastAPI backend
./scripts/deploy-server.ps1 -ProjectId <your-gcp-project-id>

# 3. Deploy the Next.js dashboard (pass the server URL from step 2)
./scripts/deploy-web.ps1 -ProjectId <your-gcp-project-id> `
                        -ApiUrl <server-url-from-step-2>

# 4. Re-run step 2 with -WebOrigin <dashboard-url> so CORS lets the dashboard call the API
./scripts/deploy-server.ps1 -ProjectId <your-gcp-project-id> `
                            -WebOrigin <dashboard-url-from-step-3>
```

To run against a **real Dynatrace tenant** instead of the bundled mocks, pass
your tenant credentials to the deploy script:

```powershell
./scripts/deploy-server.ps1 `
    -ProjectId <your-gcp-project-id> `
    -DynatraceTenantUrl https://YOUR_TENANT.live.dynatrace.com `
    -DynatraceApiToken dt0c01.YOUR_TOKEN `
    -MockMode:$false
```

The token is stored in Secret Manager — never as a plain env var.

## Repository layout

| Path | Purpose |
|---|---|
| [`server/app/main.py`](server/app/main.py) | FastAPI entrypoint, lifespan, routes |
| [`server/app/agent.py`](server/app/agent.py) | The two-phase ADK `SequentialAgent` |
| [`server/app/prompts.py`](server/app/prompts.py) | Investigation / planning / postmortem prompts |
| [`server/app/mcp_client.py`](server/app/mcp_client.py) | Dynatrace MCP wrapper (live + mock) |
| [`server/app/dynatrace_mock.py`](server/app/dynatrace_mock.py) | Bundled bad-deploy fixture data |
| [`server/app/store.py`](server/app/store.py) | Firestore repo with in-memory fallback |
| [`server/app/routes/`](server/app/routes/) | Webhook, incidents, approvals, demo, health |
| [`web/app/`](web/app/) | Next.js App Router pages |
| [`web/components/`](web/components/) | Dashboard UI |
| [`demo/scenarios/bad-deploy.md`](demo/scenarios/bad-deploy.md) | Submission video scenario + shot list |
| [`scripts/`](scripts/) | `bootstrap.ps1`, `deploy-server.ps1`, `deploy-web.ps1` |

## Submission checklist

- [x] Open-source repo (this) with Apache 2.0 license at the root
- [x] Built with Gemini + Google Cloud Agent Builder
- [x] Meaningful integration with a partner MCP server (Dynatrace)
- [x] Functional end-to-end agent (investigation → plan → approval → execution → verification → postmortem)
- [x] Polished dashboard UI for the human-in-the-loop flow
- [x] Self-contained demo scenario (no live tenant required)
- [x] Hosted public URL for judging — <https://triage-web-407454021889.us-central1.run.app>
- [x] 3-minute demo video on YouTube — <https://youtu.be/d-9pDGW1zUs>
- [x] Devpost write-up — draft submitted (final Submit pending operator review before 2026-06-11)

## License

Apache 2.0 — see [LICENSE](LICENSE).
