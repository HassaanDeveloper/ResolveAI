"use client";

import * as React from "react";
import { cn } from "cn";
import { Database, ChevronDown, ChevronRight, CheckCircle, XCircle, Clock } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";

interface ToolCallRecord {
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  success: boolean;
  error?: string;
  timestamp: string;
}

const toolDisplayNames: Record<string, string> = {
  get_order: "Retrieve Order",
  check_shipment: "Check Shipment Status",
  search_company_policy: "Search Company Policy",
  calculate_refund: "Calculate Refund Amount",
  issue_refund: "Issue Refund",
  cancel_order: "Cancel Order",
  create_escalation: "Create Escalation",
  verify_refund: "Verify Refund",
  verify_cancellation: "Verify Cancellation",
};

interface ToolCallCardProps {
  call: ToolCallRecord;
  index?: number;
  className?: string;
}

export function ToolCallCard({ call, index, className }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const displayName = toolDisplayNames[call.tool_name] || call.tool_name.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className="p-3 border-b border-border-default bg-surface-base/50">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {index !== undefined && (
              <span className="text-body-sm text-muted-foreground font-mono w-6 text-right">#{index + 1}</span>
            )}
            <Database className="h-4 w-4 text-muted-foreground flex-shrink-0" aria-hidden="true" />
            <span className="text-h2 font-medium truncate">{displayName}</span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <StatusBadge status={call.success ? "completed" : "failed"} size="sm" />
            <button
              type="button"
              className="p-1.5 rounded hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-expanded={isExpanded}
              aria-label={isExpanded ? "Collapse details" : "Expand details"}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
          </div>
        </div>

        <div className="mt-2 flex items-center gap-3 text-body-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" aria-hidden="true" />
            {call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : "—"}
          </span>
          {call.error && (
            <span className="flex items-center gap-1 text-status-deny">
              <XCircle className="h-3 w-3" aria-hidden="true" />
              Failed: {call.error}
            </span>
          )}
        </div>
      </div>

      <div
        className="overflow-hidden transition-all duration-150 ease-out"
        style={{ maxHeight: isExpanded ? "500px" : "0", opacity: isExpanded ? 1 : 0 }}
      >
        <div className="p-4 space-y-4 bg-surface-base/30">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Input</p>
              <pre className="text-code bg-muted p-3 rounded overflow-x-auto max-h-60"><code>{JSON.stringify(call.input_data, null, 2)}</code></pre>
            </div>
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Output</p>
              <pre className="text-code bg-muted p-3 rounded overflow-x-auto max-h-60">
                <code>{call.output_data ? JSON.stringify(call.output_data, null, 2) : "—"}</code>
              </pre>
            </div>
          </div>

          {call.error && (
            <div className="space-y-1 p-3 rounded bg-status-deny/5 border border-status-deny/20">
              <p className="text-label text-status-deny">Error Details</p>
              <p className="text-body-sm text-status-deny font-mono">{call.error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}