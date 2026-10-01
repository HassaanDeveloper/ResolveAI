"use client";

import { cn } from "cn";
import { Shield, Clock, CheckCircle, XCircle, User, AlertTriangle, Gavel } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import { RiskBadge } from "@/components/ui/risk-badge";

interface ApprovalRecord {
  approval_id?: string;
  status: string;
  requested_at?: string;
  decided_at?: string;
  decided_by?: string;
  reason?: string;
  action_type?: string;
  policy_rule?: string;
  risk_level?: string;
}

interface ApprovalSectionProps {
  approval?: ApprovalRecord;
  approvalRequired?: boolean;
  className?: string;
}

export function ApprovalSection({ approval, approvalRequired, className }: ApprovalSectionProps) {
  if (!approvalRequired && !approval) {
    return (
      <div className={cn("border border-border-default rounded-lg bg-surface-card p-4", className)}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-status-complete/10 text-status-complete" aria-hidden="true">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <p className="text-h2 font-medium text-foreground">Approval Not Required</p>
            <p className="text-body-sm text-muted-foreground">This request did not require human approval to proceed.</p>
          </div>
        </div>
      </div>
    );
  }

  if (!approval) {
    return (
      <div className={cn("border border-border-default rounded-lg bg-surface-card p-4", className)}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-status-wait/10 text-status-wait" aria-hidden="true">
            <Clock className="h-5 w-5" />
          </div>
          <div>
            <p className="text-h2 font-medium text-foreground">Approval Pending</p>
            <p className="text-body-sm text-muted-foreground">Waiting for human review...</p>
          </div>
        </div>
      </div>
    );
  }

  const statusConfig = {
    pending: { icon: Clock, label: "Pending Review", description: "Waiting for human decision", color: "wait" },
    approved: { icon: CheckCircle, label: "Approved", description: "Authorized by human operator", color: "complete" },
    rejected: { icon: XCircle, label: "Rejected", description: "Denied by human operator", color: "deny" },
    executed: { icon: CheckCircle, label: "Executed", description: "Approved and executed", color: "complete" },
    failed: { icon: AlertTriangle, label: "Failed", description: "Execution failed after approval", color: "deny" },
  } as const;

  const config = statusConfig[approval.status as keyof typeof statusConfig] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className={cn(
        "px-4 py-3 flex items-center gap-3 border-b border-border-default",
        config.color === "complete" && "bg-status-complete/5",
        config.color === "deny" && "bg-status-deny/5",
        config.color === "wait" && "bg-status-wait/5",
      )}>
        <div className={cn(
          "p-2 rounded-lg flex-shrink-0",
          config.color === "complete" && "bg-status-complete/10 text-status-complete",
          config.color === "deny" && "bg-status-deny/10 text-status-deny",
          config.color === "wait" && "bg-status-wait/10 text-status-wait",
        )} aria-hidden="true">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <p className="text-h2 font-medium text-foreground">{config.label}</p>
          <p className="text-body-sm text-muted-foreground">{config.description}</p>
        </div>
        <StatusBadge status={approval.status as "pending" | "approved" | "rejected" | "executed" | "failed"} size="md" />
      </div>

      <div className="p-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {approval.approval_id && (
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Approval ID</p>
              <p className="text-mono">{approval.approval_id.slice(0, 12)}...</p>
            </div>
          )}
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Risk Level</p>
            <RiskBadge level={(approval.risk_level as "LOW" | "MEDIUM" | "HIGH") || "MEDIUM"} />
          </div>
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Policy Rule</p>
            <p className="text-mono text-sm">{approval.policy_rule || "—"}</p>
          </div>
          {approval.action_type && (
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Action</p>
              <p className="text-body-sm capitalize">{approval.action_type.replace(/_/g, " ")}</p>
            </div>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Requested At</p>
            <p className="text-mono">{approval.requested_at ? new Date(approval.requested_at).toLocaleString() : "—"}</p>
          </div>
          {approval.decided_at && (
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Decided At</p>
              <p className="text-mono">{new Date(approval.decided_at).toLocaleString()}</p>
            </div>
          )}
          {approval.decided_by && (
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Decided By</p>
              <p className="flex items-center gap-1 text-body-sm">
                <User className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
                {approval.decided_by}
              </p>
            </div>
          )}
        </div>

        {approval.reason && (
          <div className="space-y-2 pt-2 border-t border-border-default">
            <p className="text-label text-muted-foreground">Decision Reason</p>
            <p className="text-body whitespace-pre-wrap">{approval.reason}</p>
          </div>
        )}

        {approval.status === "pending" && (
          <div className="pt-2 border-t border-border-default">
            <div className="p-3 rounded-lg bg-status-wait/5 border border-status-wait/20">
              <div className="flex items-center gap-2">
                <Gavel className="h-4 w-4 text-status-wait" aria-hidden="true" />
                <p className="text-body-sm text-status-wait">
                  <strong>Human-in-the-loop gate:</strong> This action requires explicit human authorization before execution.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}