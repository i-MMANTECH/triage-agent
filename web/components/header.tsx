import Link from "next/link";
import { Activity } from "lucide-react";
import { SeedDemoButton } from "@/components/seed-demo-button";

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b bg-[var(--color-background)]/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-[var(--color-primary)]/15 ring-1 ring-[var(--color-primary)]/40">
            <Activity className="h-4 w-4 text-[var(--color-primary)]" />
          </span>
          <span className="text-base font-semibold tracking-tight">Triage</span>
          <span className="hidden text-sm text-[var(--color-muted-foreground)] sm:inline">
            · On-call's AI first responder
          </span>
        </Link>
        <SeedDemoButton />
      </div>
    </header>
  );
}
