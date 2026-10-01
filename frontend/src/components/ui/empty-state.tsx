"use client";

import * as React from "react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon | React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "ghost";
  };
  className?: string;
}

export function EmptyState({ title, description, icon, action, className }: EmptyStateProps) {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) {
      return React.cloneElement(icon as React.ReactElement<Record<string, unknown>>, { className: "h-12 w-12 mx-auto" });
    }
    if (typeof icon === "function") {
      return React.createElement(icon as React.ComponentType<Record<string, unknown>>, { className: "h-12 w-12 mx-auto" });
    }
    return icon;
  };

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center py-12 px-4",
        "bg-surface-card border border-border-default rounded-lg",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      {renderIcon() && (
        <div className="mb-4 text-muted-foreground/50" aria-hidden="true">
          {renderIcon()}
        </div>
      )}
      <h3 className="text-h2 text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-body text-muted-foreground max-w-md mb-6">{description}</p>
      )}
      {action && (
        <Button
          variant={action.variant || "default"}
          onClick={action.onClick}
          className="w-auto"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}