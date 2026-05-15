import type { ApprovalRequest, Incident } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  listIncidents: () => request<Incident[]>("/incidents"),
  getIncident: (id: string) => request<Incident>(`/incidents/${id}`),
  seedDemo: () =>
    request<{ incident_id: string; scenario: string }>("/demo/seed", {
      method: "POST",
    }),
  reset: () => request<{ deleted: number }>("/demo/reset", { method: "POST" }),
  approve: (incidentId: string, body: ApprovalRequest, actionIndex = 0) =>
    request<{ status: string; incident_id: string; action_index: number }>(
      `/approvals/${incidentId}?action_index=${actionIndex}`,
      { method: "POST", body: JSON.stringify(body) },
    ),
};

export function incidentStreamUrl(id: string): string {
  return `${API_URL}/incidents/${id}/stream`;
}
