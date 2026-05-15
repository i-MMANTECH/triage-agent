import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[var(--color-secondary)] text-[var(--color-secondary-foreground)]",
        success:
          "border-transparent bg-[var(--color-success)]/15 text-[var(--color-success)] ring-1 ring-[var(--color-success)]/30",
        warning:
          "border-transparent bg-[var(--color-warning)]/15 text-[var(--color-warning)] ring-1 ring-[var(--color-warning)]/30",
        danger:
          "border-transparent bg-[var(--color-destructive)]/15 text-[var(--color-destructive)] ring-1 ring-[var(--color-destructive)]/30",
        info:
          "border-transparent bg-[var(--color-primary)]/15 text-[var(--color-primary)] ring-1 ring-[var(--color-primary)]/30",
        outline:
          "border-[var(--color-border)] text-[var(--color-foreground)]",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
