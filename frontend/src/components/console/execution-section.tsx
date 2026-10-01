"use client";

import { cn } from "cn";
import { Settings, Database, CheckCircle, XCircle, Clock, ChevronDown, ChevronRight, AlertTriangle } from "lucide-react";
import * as React from "react";
import { StatusBadge } from "@/components/ui/status-badge";

interface ToolCallRecord {
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  success: boolean;
  error?: string;
  timestamp: string;
}

interface ExecutionSectionProps {
  toolCalls: ToolCallRecord[];
  actionTaken?: string;
  actionResult?: Record<string, unknown>;
  className?: string;
}

interface ToolDisplayInfo {
  label: string;
  icon: React.ElementType;
}

const toolDisplayNames: Record<string, ToolDisplayInfo> = {
  get_order: { label: "Retrieve Order", icon: Database },
  check_shipment: { label: "Check Shipment Status", icon: Database },
  search_company_policy: { label: "Search Company Policy", icon: Settings },
  calculate_refund: { label: "Calculate Refund Amount", icon: Settings },
  issue_refund: { label: "Issue Refund", icon: CheckCircle },
  cancel_order: { label: "Cancel Order", icon: XCircle },
  create_escalation: { label: "Create Escalation", icon: AlertTriangle },
  verify_refund: { label: "Verify Refund", icon: CheckCircle },
  verify_cancellation: { label: "Verify Cancellation", icon: CheckCircle },
};

function ToolCallItem({ call, index }: { call: ToolCallRecord; index: number }) {
  const display = toolDisplayNames[call.tool_name] || {
    label: call.tool_name.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    icon: Settings,
  };
  const [isExpanded, setIsExpanded] = React.useState(false);
  const IconComponent = display.icon;

  return (
    <div
      key={index}
      className="border border-border-default rounded-lg bg-surface-card overflow-hidden"
      role="listitem"
    >
      <div className="p-3 border-b border-border-default bg-surface-base/50">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-body-sm text-muted-foreground font-mono w-6 text-right">#{index + 1}</span>
            <IconComponent className="text-muted-foreground flex-shrink-0" aria-hidden="true" />
            <span className="text-h2 font-medium truncate">{display.label}</span>
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

export function ExecutionSection({ toolCalls, actionTaken, actionResult, className }: ExecutionSectionProps) {
  if ((!toolCalls || toolCalls.length === 0) && !actionResult) {
    return (
      <div className={cn("border border-border-default rounded-lg bg-surface-card p-4", className)}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-muted/50 text-muted-foreground" aria-hidden="true">
            <Settings className="h-5 w-5" />
          </div>
          <div>
            <p className="text-h2 font-medium text-foreground">No Execution Performed</p>
            <p className="text-body-sm text-muted-foreground">No business actions were executed for this resolution.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-label text-muted-foreground">Execution</h3>
        {actionTaken && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-body-sm font-medium bg-muted text-muted-foreground">
            {actionTaken.replace(/_/g, " ")}
          </span>
        )}
      </div>

      {toolCalls && toolCalls.length > 0 && (
        <div className="space-y-2" role="list" aria-label="Tool execution steps">
          {toolCalls.map((call, index) => (
            <ToolCallItem key={index} call={call} index={index} />
          ))}
        </div>
      )}

      {actionResult && (
        <div className="border border-border-default rounded-lg bg-surface-card overflow-hidden">
          <div className="p-3 border-b border-border-default bg-surface-base/50">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-status-complete" aria-hidden="true" />
              <span className="text-h2 font-medium">Action Result</span>
            </div>
          </div>
          <div className="p-4">
            <details>
              <summary className="text-body-sm text-primary hover:text-primary/80 cursor-pointer mb-2">
                View raw action result
              </summary>
              <pre className="text-code bg-muted p-3 rounded overflow-x-auto max-h-60"><code>{JSON.stringify(actionResult, null, 2)}</code></pre>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}