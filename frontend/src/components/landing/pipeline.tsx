"use client";

import { WORKFLOW_STAGES } from "@/components/console/workflow-progress";
import { StagedGroup, StagedItem } from "@/components/landing/motion";
import { cn } from "@/lib/utils";

/**
 * Pipeline diagram of the real resolution workflow.
 *
 * The step list is imported from the Resolution Console's Workflow Progress
 * component, so this page and the product can never disagree about stage names,
 * order, or descriptions. Nothing here is illustrative.
 */

/**
 * Phase tint per stage, using existing Phase 1A status tokens only.
 * Intake is neutral; the decision-critical middle (evidence, policy, approval)
 * carries the accents; the tail returns to neutral.
 */
const PHASE: Record<string, string> = {
  request: "bg-muted text-muted-foreground border-border-default",
  understanding: "bg-muted text-muted-foreground border-border-default",
  investigating: "bg-muted text-muted-foreground border-border-default",
  evidence: "bg-status-evidence/10 text-status-evidence border-status-evidence/30",
  policy: "bg-status-policy/10 text-status-policy border-status-policy/30",
  approval: "bg-status-wait/10 text-status-wait border-status-wait/30",
  execute: "bg-status-progress/10 text-status-progress border-status-progress/30",
  verify: "bg-status-complete/10 text-status-complete border-status-complete/30",
  audit: "bg-muted text-muted-foreground border-border-default",
};
export function ResolutionPipeline() {
  const lastIndex = WORKFLOW_STAGES.length - 1;

  return (
    <StagedGroup step={60} threshold={0.15} className="relative">
      {/* Horizontal rail, shown only when all nine stages sit in one row. */}
      <span
        aria-hidden="true"
        className="pointer-events-none absolute left-0 right-0 top-3 hidden h-px bg-border-default xl:block"
      />

      <ol className="relative grid gap-y-7 md:grid-cols-3 md:gap-x-6 xl:grid-cols-9 xl:gap-y-0 xl:gap-x-0">
        {WORKFLOW_STAGES.map((stage, index) => {
          const Icon = stage.icon;
          const isLast = index === lastIndex;

          return (
            <StagedItem
              key={stage.key}
              index={index}
              as="li"
              className="group relative flex gap-4 xl:flex-col xl:items-center xl:gap-3 xl:px-1 xl:text-center"
            >
              {/* Single-column connector to the next stage. */}
              {!isLast && (
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute bottom-[-1.75rem] left-[11px] top-9 w-px bg-border-default md:hidden"
                />
              )}

              <span
                aria-hidden="true"
                className={cn(
                  "relative z-10 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border transition-transform duration-200 motion-reduce:transition-none xl:h-7 xl:w-7",
                  "group-hover:scale-105 motion-reduce:group-hover:scale-100",
                  PHASE[stage.key]
                )}
              >
                <Icon className="h-3.5 w-3.5" />
              </span>

              <div className="min-w-0 pb-1 xl:pb-0">
                <span className="block text-mono text-[0.625rem] font-medium tracking-[0.12em] text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="mt-1 block text-body-sm font-semibold leading-tight text-foreground">
                  {stage.label}
                </span>
                <span className="mt-1 block text-body-sm leading-snug text-muted-foreground xl:text-xs">
                  {stage.description}
                </span>
                <span className="mt-2 hidden text-mono text-[0.625rem] tracking-[0.12em] text-muted-foreground xl:inline">
                  {stage.shortLabel}
                </span>
              </div>
            </StagedItem>
          );
        })}
      </ol>
    </StagedGroup>
  );
}
