"use client";

import { cn } from "cn";
import { CheckCircle, XCircle, Gavel } from "lucide-react";

export type PolicyDecision = "ALLOW" | "DENY" | "REQUIRES_APPROVAL";

interface DecisionConfig {
  label: string;
  icon: React.ElementType;
  variant: "complete" | "deny" | "policy";
}

const decisionMap: Record<PolicyDecision, DecisionConfig> = {
  ALLOW: { label: "Allowed", icon: CheckCircle, variant: "complete" },
  DENY: { label: "Denied", icon: XCircle, variant: "deny" },
  REQUIRES_APPROVAL: { label: "Approval required", icon: Gavel, variant: "policy" },
};

const variantClasses: Record<"complete" | "deny" | "policy", string> = {
  complete: "bg-status-complete text-status-complete-foreground",
  deny: "bg-status-deny text-status-deny-foreground",
  policy: "bg-status-policy text-status-policy-foreground",
};

interface DecisionBadgeProps {
  decision: PolicyDecision;
  showIcon?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export function DecisionBadge({
  decision,
  showIcon = true,
  size = "md",
  className,
}: DecisionBadgeProps) {
  const config = decisionMap[decision] || {
    label: "Unknown",
    icon: Gavel,
    variant: "policy" as const,
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

export { decisionMap };
export type { DecisionBadgeProps };