# Demo

Materials for the 3-minute submission video.

The canonical scenario is **bad-deploy**: a fictional `shop-checkout` service
deploys a regression that causes `POST /checkout` to start returning 500s.
Dynatrace fires a problem. Triage receives it, identifies the bad deploy via
the MCP toolchain, proposes a rollback, the operator approves, and the
service recovers — all in under three minutes.

The scenario data lives in
[`../server/app/dynatrace_mock.py`](../server/app/dynatrace_mock.py) and is
fully self-contained: no live Dynatrace tenant is required to drive the demo.

| File | Purpose |
|---|---|
| [`scenarios/bad-deploy.md`](scenarios/bad-deploy.md) | Scene-by-scene description, timing budget, and the recording shot list. |

## Driving the demo on camera

1. Start backend + frontend per the root [README](../README.md#quickstart--run-locally-in-five-minutes).
2. Open <http://localhost:3000>.
3. Click **Seed demo incident** in the header — this calls `POST /demo/seed`.
4. Cut to the incident detail page and let the timeline fill in.
5. When the approval card appears, click **Approve & execute**.
6. The status flips to Executing → Verifying → Resolved. Scroll to the
   postmortem.

Reset between takes:

```bash
curl -X POST http://localhost:8080/demo/reset
```
