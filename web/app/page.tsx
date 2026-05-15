import { IncidentList } from "@/components/incident-list";
import { api } from "@/lib/api";
import type { Incident } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let incidents: Incident[] = [];
  let error: string | null = null;
  try {
    incidents = await api.listIncidents();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to fetch incidents";
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Incidents</h1>
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Live view of every Dynatrace problem Triage has picked up. Click an
          incident to see the agent's plan and approve actions.
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-[var(--color-destructive)]/40 bg-[var(--color-destructive)]/10 p-4 text-sm">
          <p className="font-medium">Could not reach the API.</p>
          <p className="mt-1 text-[var(--color-muted-foreground)]">{error}</p>
          <p className="mt-2 font-mono text-xs text-[var(--color-muted-foreground)]">
            NEXT_PUBLIC_API_URL ={" "}
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"}
          </p>
        </div>
      ) : (
        <IncidentList incidents={incidents} />
      )}
    </div>
  );
}
