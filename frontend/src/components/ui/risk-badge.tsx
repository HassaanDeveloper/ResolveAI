"use client";

import { cn } from "cn";
import { Shield, AlertTriangle } from "lucide-react";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

interface RiskConfig {
  label: string;
  icon: React.ElementType;
  variant: "complete" | "wait" | "deny";
}

const riskMap: Record<RiskLevel, RiskConfig> = {
  LOW: { label: "Low", icon: Shield, variant: "complete" },
  MEDIUM: { label: "Medium", icon: AlertTriangle, variant: "wait" },
  HIGH: { label: "High", icon: AlertTriangle, variant: "deny" },
};

const variantClasses: Record<"complete" | "wait" | "deny", string> = {
  complete: "bg-status-complete text-status-complete-foreground",
  wait: "bg-status-wait text-status-wait-foreground",
  deny: "bg-status-deny text-status-deny-foreground",
};

interface RiskBadgeProps {
  level: RiskLevel;
  showIcon?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export function RiskBadge({ level, showIcon = true, size = "md", className }: RiskBadgeProps) {
  const config = riskMap[level] || {
    label: "Unknown",
    icon: AlertTriangle,
    variant: "wait" as const,
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

export { riskMap };
export type { RiskBadgeProps };