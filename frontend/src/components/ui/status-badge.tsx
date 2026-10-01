"use client";

import { cn } from "cn";
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
  Search,
  Database,
  Gavel,
  Shield,
  Settings,
  ClipboardCheck,
} from "lucide-react";

export type WorkflowStatus =
  | "pending"
  | "understanding"
  | "investigating"
  | "retrieving_policy"
  | "deciding"
  | "policy_check"
  | "pending_approval"
  | "executing"
  | "verifying"
  | "completed"
  | "rejected"
  | "failed";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "executed" | "failed";

export type StatusVariant =
  | "complete"
  | "progress"
  | "wait"
  | "deny"
  | "policy"
  | "evidence";

interface StatusConfig {
  label: string;
  icon: React.ElementType;
  variant: StatusVariant;
}

const workflowStatusMap: Record<WorkflowStatus, StatusConfig> = {
  pending: { label: "Pending", icon: Clock, variant: "wait" },
  understanding: { label: "Understanding", icon: Settings, variant: "progress" },
  investigating: { label: "Investigating", icon: Search, variant: "progress" },
  retrieving_policy: { label: "Retrieving policy", icon: Database, variant: "wait" },
  deciding: { label: "Deciding", icon: Gavel, variant: "progress" },
  policy_check: { label: "Policy check", icon: Gavel, variant: "policy" },
  pending_approval: { label: "Approval required", icon: Shield, variant: "wait" },
  executing: { label: "Executing", icon: Database, variant: "progress" },
  verifying: { label: "Verifying", icon: ClipboardCheck, variant: "progress" },
  completed: { label: "Completed", icon: CheckCircle, variant: "complete" },
  rejected: { label: "Rejected", icon: XCircle, variant: "deny" },
  failed: { label: "Failed", icon: AlertTriangle, variant: "deny" },
};

const approvalStatusMap: Record<ApprovalStatus, StatusConfig> = {
  pending: { label: "Pending", icon: Clock, variant: "wait" },
  approved: { label: "Approved", icon: CheckCircle, variant: "complete" },
  rejected: { label: "Rejected", icon: XCircle, variant: "deny" },
  executed: { label: "Executed", icon: ClipboardCheck, variant: "complete" },
  failed: { label: "Failed", icon: AlertTriangle, variant: "deny" },
};

const variantClasses: Record<StatusVariant, string> = {
  complete: "bg-status-complete text-status-complete-foreground",
  progress: "bg-status-progress text-status-progress-foreground",
  wait: "bg-status-wait text-status-wait-foreground",
  deny: "bg-status-deny text-status-deny-foreground",
  policy: "bg-status-policy text-status-policy-foreground",
  evidence: "bg-status-evidence text-status-evidence-foreground",
};

interface StatusBadgeProps {
  status: WorkflowStatus | ApprovalStatus;
  showIcon?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({
  status,
  showIcon = true,
  size = "md",
  className,
}: StatusBadgeProps) {
  const config =
    workflowStatusMap[status as WorkflowStatus] ||
    approvalStatusMap[status as ApprovalStatus] || {
      label: String(status).replace(/_/g, " "),
      icon: AlertTriangle,
      variant: "deny" as StatusVariant,
    };

  const Icon = config.icon;
  const variantClass = variantClasses[config.variant];
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs gap-1" : "px-2.5 py-1 text-sm gap-1.5";

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-md border",
        "border-transparent",
        variantClass,
        sizeClass,
        className,
      )}
      role="status"
      aria-live="polite"
    >
      {showIcon && <Icon className={cn("shrink-0", size === "sm" ? "h-3 w-3" : "h-4 w-4")} aria-hidden="true" />}
      <span>{config.label}</span>
    </span>
  );
}

export { workflowStatusMap, approvalStatusMap };
export type { StatusBadgeProps };