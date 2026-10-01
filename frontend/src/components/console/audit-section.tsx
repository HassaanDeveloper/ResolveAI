"use client";

import { cn } from "cn";
import { ChevronDown, ChevronRight, FileText, Hash, AlertTriangle, CheckCircle } from "lucide-react";
import * as React from "react";

interface AuditEvent {
  id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  created_at: string;
}

interface AuditSectionProps {
  workflowId: string;
  requestId: string;
  events?: AuditEvent[];
  className?: string;
}

const eventTypeLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  request_received: { label: "Request Received", icon: <FileText className="h-4 w-4" />, color: "text-muted-foreground" },
  intent_identified: { label: "Intent Identified", icon: <Hash className="h-4 w-4" />, color: "text-primary" },
  order_retrieved: { label: "Order Retrieved", icon: <FileText className="h-4 w-4" />, color: "text-status-progress" },
  shipment_checked: { label: "Shipment Checked", icon: <FileText className="h-4 w-4" />, color: "text-status-progress" },
  policy_retrieved: { label: "Policy Retrieved", icon: <FileText className="h-4 w-4" />, color: "text-status-evidence" },
  refund_calculated: { label: "Refund Calculated", icon: <Hash className="h-4 w-4" />, color: "text-status-progress" },
  policy_evaluated: { label: "Policy Evaluated", icon: <CheckCircle className="h-4 w-4" />, color: "text-status-policy" },
  approval_requested: { label: "Approval Requested", icon: <AlertTriangle className="h-4 w-4" />, color: "text-status-wait" },
  approval_granted: { label: "Approval Granted", icon: <CheckCircle className="h-4 w-4" />, color: "text-status-complete" },
  approval_rejected: { label: "Approval Rejected", icon: <AlertTriangle className="h-4 w-4" />, color: "text-status-deny" },
  action_executed: { label: "Action Executed", icon: <CheckCircle className="h-4 w-4" />, color: "text-status-complete" },
  action_verified: { label: "Action Verified", icon: <CheckCircle className="h-4 w-4" />, color: "text-status-complete" },
  workflow_completed: { label: "Workflow Completed", icon: <CheckCircle className="h-4 w-4" />, color: "text-status-complete" },
  workflow_failed: { label: "Workflow Failed", icon: <AlertTriangle className="h-4 w-4" />, color: "text-status-deny" },
  error_occurred: { label: "Error Occurred", icon: <AlertTriangle className="h-4 w-4" />, color: "text-status-deny" },
  escalation_created: { label: "Escalation Created", icon: <AlertTriangle className="h-4 w-4" />, color: "text-status-wait" },
};

export function AuditSection({ workflowId, events, className }: AuditSectionProps) {
  const [showAll, setShowAll] = React.useState(false);
  const displayEvents = events || [];
  const visibleEvents = showAll ? displayEvents : displayEvents.slice(0, 5);

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className="px-4 py-3 border-b border-border-default bg-surface-base/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
            <div>
              <p className="text-h2 font-medium text-foreground">Audit Trail</p>
              <p className="text-body-sm text-muted-foreground">
                {displayEvents.length} event{displayEvents.length !== 1 ? "s" : ""} recorded
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="space-y-1 text-right hidden sm:block">
              <p className="text-label text-muted-foreground">Workflow ID</p>
              <p className="text-mono text-sm">{workflowId.slice(0, 16)}...</p>
            </div>
            {displayEvents.length > 5 && (
              <button
                type="button"
                className="flex items-center gap-1 text-body-sm text-primary hover:text-primary/80 px-2 py-1 rounded hover:bg-primary/5 transition-colors"
                onClick={() => setShowAll(!showAll)}
                aria-expanded={showAll}
              >
                {showAll ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                {showAll ? "Show less" : `Show all ${displayEvents.length}`}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="divide-y divide-border-default">
        {displayEvents.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" aria-hidden="true" />
            <p className="text-body text-muted-foreground">No audit events available</p>
            <p className="text-body-sm text-muted-foreground mt-1">Audit events will appear here as the resolution progresses.</p>
          </div>
        ) : (
          <>
            {visibleEvents.map((event) => {
              const config = eventTypeLabels[event.event_type] || {
                label: event.event_type.replace(/_/g, " "),
                icon: <FileText className="h-4 w-4" />,
                color: "text-muted-foreground",
              };

              return (
                <div
                  key={event.id}
                  className="p-3 hover:bg-muted/30 transition-colors flex items-start gap-3"
                  role="listitem"
                >
                  <div className={cn("p-1.5 rounded flex-shrink-0", config.color)}>
                    {config.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-body font-medium truncate">{config.label}</p>
                      <span className="text-body-sm text-muted-foreground font-mono flex-shrink-0">
                        {event.created_at ? new Date(event.created_at).toLocaleTimeString() : "—"}
                      </span>
                    </div>
                    {Object.keys(event.event_data).length > 0 && (
                      <details className="mt-1">
                        <summary className="text-body-sm text-muted-foreground cursor-pointer hover:text-foreground">
                          View event data
                        </summary>
                        <pre className="mt-1 text-code bg-muted/50 p-2 rounded overflow-x-auto max-h-32"><code>{JSON.stringify(event.event_data, null, 2)}</code></pre>
                      </details>
                    )}
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>

      {displayEvents.length > 5 && !showAll && (
        <div className="p-3 border-t border-border-default bg-surface-base/50 text-center">
          <button
            type="button"
            className="text-body-sm text-primary hover:text-primary/80"
            onClick={() => setShowAll(true)}
          >
            Show all {displayEvents.length} events
          </button>
        </div>
      )}
    </div>
  );
}