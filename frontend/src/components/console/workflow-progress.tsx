"use client";

import { cn } from "cn";
import { CheckCircle, Settings, Search, Database, Gavel, Shield, ClipboardCheck } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";

export type WorkflowStageKey =
  | "request"
  | "understanding"
  | "investigating"
  | "evidence"
  | "policy"
  | "approval"
  | "execute"
  | "verify"
  | "audit";

export interface WorkflowStage {
  key: WorkflowStageKey;
  label: string;
  shortLabel: string;
  icon: React.ElementType;
  description: string;
}

export const WORKFLOW_STAGES: WorkflowStage[] = [
  { key: "request", label: "Request", shortLabel: "REQ", icon: Settings, description: "Customer request received" },
  { key: "understanding", label: "Understand", shortLabel: "UND", icon: Settings, description: "Extract order ID & classify intent" },
  { key: "investigating", label: "Investigate", shortLabel: "INV", icon: Search, description: "Retrieve order & shipping status" },
  { key: "evidence", label: "Evidence", shortLabel: "EVD", icon: Database, description: "Retrieve policy evidence" },
  { key: "policy", label: "Policy", shortLabel: "POL", icon: Gavel, description: "Run deterministic policy engine" },
  { key: "approval", label: "Approval", shortLabel: "APR", icon: Shield, description: "Human review if required" },
  { key: "execute", label: "Execute", shortLabel: "EXE", icon: Database, description: "Perform authorized action" },
  { key: "verify", label: "Verify", shortLabel: "VER", icon: ClipboardCheck, description: "Confirm action succeeded" },
  { key: "audit", label: "Audit", shortLabel: "AUD", icon: CheckCircle, description: "Record for auditability" },
];

const statusOrder: WorkflowStageKey[] = [
  "request",
  "understanding",
  "investigating",
  "evidence",
  "policy",
  "approval",
  "execute",
  "verify",
  "audit",
];

function getToolCallStage(toolCalls: unknown[]): WorkflowStageKey | null {
  if (!toolCalls || toolCalls.length === 0) return null;
  const calls = toolCalls as Array<{ tool_name?: string }>;
  const lastToolName = calls[calls.length - 1].tool_name || "";
  if (lastToolName === "get_order" || lastToolName === "get_shipping_status") return "investigating";
  if (lastToolName === "search_company_policy") return "evidence";
  if (lastToolName === "calculate_refund") return "policy";
  if (lastToolName === "issue_refund" || lastToolName === "cancel_order") return "execute";
  return null;
}

function getStageStatusForFailed(
  stageKey: WorkflowStageKey,
  toolCalls: unknown[],
  retrievedDocuments: unknown[],
  errors: string[]
): "complete" | "progress" | "failed" | "skipped" | "wait" {
  const stageIndex = statusOrder.indexOf(stageKey);
  const lastToolStage = getToolCallStage(toolCalls);
  const lastToolIndex = lastToolStage ? statusOrder.indexOf(lastToolStage) : -1;

  if (stageIndex < lastToolIndex || (lastToolStage === null && stageIndex < statusOrder.indexOf("investigating"))) {
    return "complete";
  }
  if (stageIndex === lastToolIndex || (lastToolStage === null && stageIndex === statusOrder.indexOf("investigating"))) {
    return "failed";
  }
  return "skipped";
}

function getStageStatus(
  stageKey: WorkflowStageKey,
  currentStatus: string,
  toolCalls: unknown[],
  retrievedDocuments: unknown[],
  errors: string[]
): "complete" | "progress" | "wait" | "failed" | "skipped" {
  const statusIndex = statusOrder.findIndex((s) => {
    if (currentStatus === "pending" || currentStatus === "understanding") return s === "understanding";
    if (currentStatus === "investigating") return s === "investigating";
    if (currentStatus === "retrieving_policy") return s === "evidence";
    if (currentStatus === "deciding" || currentStatus === "policy_check") return s === "policy";
    if (currentStatus === "pending_approval") return s === "approval";
    if (currentStatus === "executing") return s === "execute";
    if (currentStatus === "verifying") return s === "verify";
    if (currentStatus === "completed") return s === "audit";
    if (currentStatus === "rejected" || currentStatus === "failed") return s === "audit";
    return -1;
  });

  const stageIndex = statusOrder.indexOf(stageKey);

  if (currentStatus === "failed") {
    return getStageStatusForFailed(stageKey, toolCalls, retrievedDocuments, errors);
  }

  if (stageIndex < statusIndex) return "complete";
  if (stageIndex === statusIndex) return "progress";
  return "wait";
}

interface WorkflowProgressProps {
  currentStatus: string;
  toolCalls?: unknown[];
  retrievedDocuments?: unknown[];
  errors?: string[];
  className?: string;
  compact?: boolean;
}

export function WorkflowProgress({
  currentStatus,
  toolCalls = [],
  retrievedDocuments = [],
  errors = [],
  className,
  compact = false,
}: WorkflowProgressProps) {
  return (
    <div className={cn("space-y-3", className)} role="list" aria-label="Resolution workflow progress">
      <div className="flex items-center justify-between">
        <h3 className="text-label text-muted-foreground">Workflow Progress</h3>
        <StatusBadge status={currentStatus as "pending" | "understanding" | "investigating" | "retrieving_policy" | "deciding" | "policy_check" | "pending_approval" | "executing" | "verifying" | "completed" | "rejected" | "failed"} size="sm" />
      </div>

      <div className={cn("space-y-2", compact && "space-y-1")}>
        {WORKFLOW_STAGES.map((stage) => {
          const stageStatus = getStageStatus(stage.key, currentStatus, toolCalls, retrievedDocuments, errors);
          const isCompleted = stageStatus === "complete";
          const isCurrent = stageStatus === "progress";
          const isFailed = stageStatus === "failed";
          const isSkipped = stageStatus === "skipped";
          const IconComponent = stage.icon;

          return (
            <div
              key={stage.key}
              className={cn(
                "flex items-center gap-3 relative",
                compact && "gap-2",
              )}
              role="listitem"
              aria-current={isCurrent ? "step" : undefined}
            >
              <div className={cn(
                "flex items-center gap-2 flex-shrink-0",
                compact && "gap-1",
              )}>
                <div className={cn(
                  "w-9 h-9 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0",
                  compact && "w-8 h-8",
                  isCompleted && "bg-status-complete text-status-complete-foreground",
                  isCurrent && "bg-status-progress text-status-progress-foreground animate-pulse",
                  isFailed && "bg-status-deny text-status-deny-foreground",
                  isSkipped && "bg-muted text-muted-foreground/50",
                  (!isCompleted && !isCurrent && !isFailed && !isSkipped) && "bg-muted text-muted-foreground",
                )}>
                  {isCompleted ? <CheckCircle className="h-4 w-4" /> : <IconComponent className="h-4 w-4" />}
                </div>

                <div className={cn("hidden md:block", compact && "hidden")}>
                  <div className="w-px h-6 bg-border-default ml-4" />
                </div>
              </div>

              <div className={cn("flex-1 min-w-0", compact && "hidden")}>
                <p className={cn(
                  "text-body font-medium truncate",
                  isCurrent ? "text-foreground" : "text-muted-foreground",
                )}>
                  {stage.label}
                </p>
                <p className="text-body-sm text-muted-foreground truncate">{stage.description}</p>
              </div>

              <div className={cn("flex-shrink-0", compact && "w-16")}>
                <span className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                  isCompleted && "bg-status-complete/10 text-status-complete",
                  isCurrent && "bg-status-progress/10 text-status-progress",
                  isFailed && "bg-status-deny/10 text-status-deny",
                  isSkipped && "bg-muted/50 text-muted-foreground",
                  (!isCompleted && !isCurrent && !isFailed && !isSkipped) && "bg-muted/50 text-muted-foreground",
                )}>
                  {stage.shortLabel}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
