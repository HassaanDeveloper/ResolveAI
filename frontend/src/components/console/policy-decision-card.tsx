"use client";

import { cn } from "cn";
import { Gavel, AlertTriangle, Shield, FileText } from "lucide-react";
import { DecisionBadge } from "@/components/ui/decision-badge";
import { RiskBadge } from "@/components/ui/risk-badge";

interface PolicyDecisionCardProps {
  policy: {
    action_type: string;
    decision: "ALLOW" | "DENY" | "REQUIRES_APPROVAL";
    reason: string;
    policy_rule: string;
    risk_level: "LOW" | "MEDIUM" | "HIGH";
    approval_tier?: string;
    conditions?: string[];
  };
  className?: string;
}

export function PolicyDecisionCard({ policy, className }: PolicyDecisionCardProps) {
  const decisionConfig = {
    ALLOW: { icon: Gavel, label: "Allowed", description: "The request complies with policy and can proceed." },
    DENY: { icon: AlertTriangle, label: "Denied", description: "The request violates policy and cannot proceed." },
    REQUIRES_APPROVAL: { icon: Shield, label: "Approval Required", description: "The request requires human authorization before proceeding." },
  } as const;

  const config = decisionConfig[policy.decision];

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className={cn(
        "px-4 py-3 flex items-center gap-3 border-b border-border-default",
        policy.decision === "ALLOW" && "bg-status-complete/5",
        policy.decision === "DENY" && "bg-status-deny/5",
        policy.decision === "REQUIRES_APPROVAL" && "bg-status-policy/5",
      )}>
        <config.icon className={cn(
          "h-5 w-5 flex-shrink-0",
          policy.decision === "ALLOW" && "text-status-complete",
          policy.decision === "DENY" && "text-status-deny",
          policy.decision === "REQUIRES_APPROVAL" && "text-status-policy",
        )} aria-hidden="true" />
        <div className="flex-1">
          <p className="text-h2 font-medium text-foreground">{config.label}</p>
          <p className="text-body-sm text-muted-foreground">{config.description}</p>
        </div>
        <DecisionBadge decision={policy.decision} size="md" />
      </div>

      <div className="p-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Action Type</p>
            <p className="text-mono capitalize">{policy.action_type.replace(/_/g, " ")}</p>
          </div>
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Risk Level</p>
            <RiskBadge level={policy.risk_level} />
          </div>
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Policy Rule</p>
            <p className="text-mono text-sm">{policy.policy_rule}</p>
          </div>
          {policy.approval_tier && (
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Approval Tier</p>
              <span className="inline-flex items-center px-2 py-1 rounded text-body-sm font-medium bg-muted text-muted-foreground">
                {policy.approval_tier}
              </span>
            </div>
          )}
        </div>

        <div className="space-y-2 pt-2 border-t border-border-default">
          <p className="text-label text-muted-foreground">Reason</p>
          <p className="text-body whitespace-pre-wrap">{policy.reason}</p>
        </div>

        {policy.conditions && policy.conditions.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-border-default">
            <p className="text-label text-muted-foreground">Conditions Evaluated</p>
            <ul className="space-y-1">
              {policy.conditions.map((condition, i) => (
                <li key={i} className="flex items-start gap-2 text-body-sm">
                  <FileText className="h-4 w-4 text-muted-foreground/50 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <span>{condition}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}