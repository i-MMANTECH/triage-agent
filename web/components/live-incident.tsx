"use client";

import { useEffect, useState } from "react";

import { incidentStreamUrl } from "@/lib/api";
import type { Incident } from "@/lib/types";

/**
 * Subscribes to the incident's SSE stream and yields the latest snapshot.
 * Falls back to the server-rendered prop while disconnected.
 */
export function useLiveIncident(initial: Incident): Incident {
  const [incident, setIncident] = useState(initial);

  useEffect(() => {
    const source = new EventSource(incidentStreamUrl(initial.id));
    source.addEventListener("update", (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data) as Incident;
        setIncident(data);
      } catch {
        /* ignore */
      }
    });
    source.addEventListener("not_found", () => source.close());
    source.onerror = () => source.close();
    return () => source.close();
  }, [initial.id]);

  return incident;
}
