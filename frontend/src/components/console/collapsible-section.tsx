"use client";

import * as React from "react";
import { cn } from "cn";

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
}

export function CollapsibleSection({
  title,
  children,
  defaultOpen = true,
  className,
  headerClassName,
  contentClassName,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  return (
    <div className={cn("border border-border-default rounded-lg overflow-hidden bg-surface-card", className)}>
      <button
        type="button"
        className={cn(
          "w-full flex items-center justify-between p-4",
          "hover:bg-muted/30 transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          headerClassName,
        )}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls={`collapsible-content-${title.replace(/\s+/g, "-").toLowerCase()}`}
      >
        <div className="flex items-center gap-3">
          <h3 className="text-h2 font-medium text-foreground">{title}</h3>
        </div>
        <span className={cn(
          "transition-transform duration-150 ease-out",
          isOpen ? "rotate-90" : "rotate-0",
        )} aria-hidden="true">
          ▼
        </span>
      </button>
      <div
        id={`collapsible-content-${title.replace(/\s+/g, "-").toLowerCase()}`}
        className={cn(
          "overflow-hidden transition-all duration-150 ease-out",
          isOpen ? "max-h-[2000px] opacity-100" : "max-h-0 opacity-0",
          contentClassName,
        )}
        role="region"
        aria-label={title}
      >
        <div className="px-4 pb-4 border-t border-border-default bg-surface-base/50">
          {children}
        </div>
      </div>
    </div>
  );
}