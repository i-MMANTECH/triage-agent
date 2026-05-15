"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function ApprovalControls({ incidentId }: { incidentId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [note, setNote] = useState("");

  function submit(decision: "approved" | "rejected") {
    setError(null);
    startTransition(async () => {
      try {
        await api.approve(incidentId, {
          decision,
          operator: "operator",
          note,
        });
        router.refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Approval failed");
      }
    });
  }

  return (
    <div className="space-y-3 rounded-lg border bg-[var(--color-muted)]/40 p-4">
      <div className="space-y-2">
        <label className="text-xs uppercase tracking-wider text-[var(--color-muted-foreground)]">
          Operator note (optional)
        </label>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="e.g. Approving — this matches the v4.2.0 deploy window."
          className="w-full resize-none rounded-md border bg-[var(--color-background)] px-3 py-2 text-sm placeholder:text-[var(--color-muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-ring)]"
        />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="success"
          onClick={() => submit("approved")}
          disabled={pending}
        >
          <Check className="h-4 w-4" />
          Approve &amp; execute
        </Button>
        <Button
          variant="outline"
          onClick={() => submit("rejected")}
          disabled={pending}
        >
          <X className="h-4 w-4" />
          Reject
        </Button>
        {pending && (
          <span className="text-xs text-[var(--color-muted-foreground)]">
            Working…
          </span>
        )}
        {error && (
          <span className="text-xs text-[var(--color-destructive)]">{error}</span>
        )}
      </div>
    </div>
  );
}
