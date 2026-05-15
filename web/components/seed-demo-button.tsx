"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function SeedDemoButton() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function handleClick() {
    setError(null);
    startTransition(async () => {
      try {
        const { incident_id } = await api.seedDemo();
        router.push(`/incidents/${incident_id}`);
        router.refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to seed");
      }
    });
  }

  return (
    <div className="flex items-center gap-3">
      {error && (
        <span className="text-xs text-[var(--color-destructive)]">{error}</span>
      )}
      <Button onClick={handleClick} disabled={pending} size="sm">
        <Sparkles className="h-3.5 w-3.5" />
        {pending ? "Seeding…" : "Seed demo incident"}
      </Button>
    </div>
  );
}
