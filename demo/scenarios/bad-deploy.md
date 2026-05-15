# Scenario: Bad deploy breaks `shop-checkout`

This is the canonical scenario for the 3-minute submission video. It is fully
self-contained — no live Dynatrace tenant required. All fixture data lives in
[`server/app/dynatrace_mock.py`](../../server/app/dynatrace_mock.py).

## Setup

A fictional Node.js service `shop-checkout` (entity ID `SERVICE-A1B2C3D4E5F6`)
serves the checkout endpoints of an e-commerce site. It is monitored by
Dynatrace. The service runs at ~2,400 requests/minute with a normal failure
rate around **0.1%**.

## The incident

| T (rel) | What happens |
|---|---|
| T-3:00 | A new version `v4.2.0` of `shop-checkout` is deployed. |
| T-2:30 | First failed `POST /checkout` requests appear in the trace stream. The error: `TypeError: Cannot read properties of undefined (reading 'currency')` at `calculateTotals (totals.js:142:18)` — a regression where a removed field is still being read. |
| T-2:00 | Failure rate crosses 5%. Dynatrace fires a "Failure rate increase" problem on the `shop-checkout` service. |
| T-1:55 | The Dynatrace problem webhook hits Triage. The incident appears on the dashboard with status **Detected**. |
| T-1:50 | Triage transitions to **Investigating** and starts calling Dynatrace MCP tools. |
| T-1:30 | Triage produces an `IncidentPlan`. Top hypothesis: "Regression in v4.2.0 of shop-checkout — `calculateTotals` reads undefined `currency` field." Proposed action: rollback to `v4.1.9`. |
| T-1:20 | The dashboard shows the approval card. The operator clicks **Approve**. |
| T-1:15 | Triage executes the rollback through the Dynatrace MCP. |
| T-0:45 | Failure rate drops back to baseline. Triage confirms recovery via metrics and writes the postmortem. |
| T-0:30 | Incident status flips to **Resolved**. |

The full arc fits comfortably inside a 3-minute video budget.

## Recording shot list

| Shot | Duration | Notes |
|---|---|---|
| 1. Title card | 0:00–0:05 | "Triage — On-call's AI first responder" + the hackathon tagline. |
| 2. Problem framing | 0:05–0:25 | Voiceover: "Every production incident starts the same way…" Cut to a slide showing the on-call pager and the dashboard side by side. |
| 3. Seed the incident | 0:25–0:35 | On camera: click **Seed demo incident** in the dashboard header (calls `POST /demo/seed`). Cut to the incident appearing in the list. |
| 4. Investigation phase | 0:35–1:10 | Cut to the incident detail page. Speed up 2x as the timeline fills in: Detected → Investigating → finding 1 (failed traces) → finding 2 (recent deploy at T-3min) → finding 3 (entity metrics). |
| 5. The plan | 1:10–1:40 | The approval card appears. Pan across: top hypothesis, blast radius, the rollback action. Voiceover names Gemini 3 + Dynatrace MCP. |
| 6. Approve | 1:40–1:50 | Click **Approve**. Status flips to **Executing** then **Verifying**. |
| 7. Recovery | 1:50–2:20 | The metric panel updates: failure rate 18.4% → 0.12%. Status flips to **Resolved**. |
| 8. Postmortem | 2:20–2:45 | Scroll through the Gemini-generated postmortem. Highlight the timeline and action items. |
| 9. Outro | 2:45–3:00 | Card with GitHub URL, hosted demo URL, and "Built with Google Cloud Agent Builder + Gemini 3 + Dynatrace MCP". |

## How to drive the demo

```bash
# Backend
cd server
cp .env.example .env       # mock mode is on by default
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd web
npm install
npm run dev
```

Open `http://localhost:3000`. Click **Seed demo incident**. The agent runs
end-to-end against the bundled mock data. No GCP credentials, no Dynatrace
tenant, no surprises during the recording.

To reset between takes:

```bash
curl -X POST http://localhost:8080/demo/reset
```
