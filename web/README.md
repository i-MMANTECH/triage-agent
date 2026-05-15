# Web

Next.js 16 dashboard for the Triage human-in-the-loop approval flow. Deployed
to Cloud Run as a standalone Node.js service. Built with Tailwind 4 and an
inline shadcn-style component layer (no CLI setup required).

## Pages

| Route | What it shows |
|---|---|
| `/` | Live list of incidents, newest first, with status pills and timing. |
| `/incidents/[id]` | Full incident detail — agent plan, approval controls, live SSE timeline, and postmortem when available. |

## Components

| File | Role |
|---|---|
| `app/layout.tsx` | Root layout, header, dark theme via `globals.css` |
| `app/page.tsx` | Server component that fetches the incident list |
| `app/incidents/[id]/page.tsx` | Server component that hydrates the detail view |
| `components/header.tsx` | Top bar with the Seed Demo button |
| `components/seed-demo-button.tsx` | Client component — calls `POST /demo/seed` |
| `components/incident-list.tsx` | Compact incident cards on the home page |
| `components/incident-detail.tsx` | The detail view, wires SSE to the rest |
| `components/live-incident.tsx` | `useLiveIncident` SSE hook |
| `components/plan-card.tsx` | The agent's structured plan, hypotheses + actions |
| `components/approval-controls.tsx` | Approve / Reject buttons |
| `components/timeline.tsx` | Iconified event timeline |
| `components/postmortem-view.tsx` | Markdown-rendered postmortem |
| `components/status-badge.tsx` | Animated status pills (live states pulse) |
| `components/ui/{button,card,badge}.tsx` | Primitive design system |
| `lib/api.ts` | Typed fetch client |
| `lib/types.ts` | TypeScript mirrors of the backend Pydantic models |
| `lib/utils.ts` | `cn`, time-formatting helpers |

## Run locally

```powershell
cd web
npm install
copy .env.example .env.local
npm run dev
```

The dashboard expects the backend on `http://localhost:8080`. Override via
`NEXT_PUBLIC_API_URL` in `.env.local`.
