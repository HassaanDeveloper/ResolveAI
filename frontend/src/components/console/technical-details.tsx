"use client";

import { cn } from "cn";
import { Code2, ChevronDown, ChevronRight, Copy, Check } from "lucide-react";
import * as React from "react";

interface TechnicalDetailsProps {
  data: Record<string, unknown>;
  label?: string;
  className?: string;
}

export function TechnicalDetails({ data, label = "Raw Response JSON", className }: TechnicalDetailsProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for environments without clipboard API
      const textarea = document.createElement("textarea");
      textarea.value = JSON.stringify(data, null, 2);
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className="p-3 border-b border-border-default bg-surface-base/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code2 className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          <span className="text-h2 font-medium">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="p-1.5 rounded hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          </button>
          <button
            type="button"
            className="p-1.5 rounded hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            onClick={handleCopy}
            aria-label="Copy JSON to clipboard"
          >
            {copied ? (
              <Check className="h-4 w-4 text-status-complete" />
            ) : (
              <Copy className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      <div
        className="overflow-hidden transition-all duration-150 ease-out"
        style={{ maxHeight: isExpanded ? "600px" : "0", opacity: isExpanded ? 1 : 0 }}
      >
        <div className="p-4 bg-surface-base/30">
          <pre className="text-code bg-muted p-3 rounded overflow-x-auto max-h-[500px]"><code>{JSON.stringify(data, null, 2)}</code></pre>
        </div>
      </div>
    </div>
  );
}