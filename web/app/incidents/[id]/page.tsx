import { notFound } from "next/navigation";

import { IncidentDetail } from "@/components/incident-detail";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function IncidentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  try {
    const incident = await api.getIncident(id);
    return <IncidentDetail initial={incident} />;
  } catch {
    notFound();
  }
}
