"use client";

import { cn } from "cn";
import { FileText, Clock, User, Hash, AlertTriangle, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import { useMemo } from "react";

interface ResolutionHeaderProps {
  result: {
    workflow_id: string;
    request_id: string;
    status: string;
    intent: string;
    user_request: string;
    order_id?: string;
    order_number?: string;
    customer_id?: string;
    final_message: string;
    errors: string[];
    created_at?: string;
    completed_at?: string;
  };
  className?: string;
}

function formatDuration(createdAt?: string, completedAt?: string) {
  if (!createdAt) return null;
  const start = new Date(createdAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const diff = end - start;
  if (diff < 1000) return "< 1s";
  if (diff < 60000) return `${Math.round(diff / 1000)}s`;
  if (diff < 3600000) return `${Math.round(diff / 60000)}m ${Math.round((diff % 60000) / 1000)}s`;
  return `${Math.round(diff / 3600000)}h ${Math.round((diff % 3600000) / 60000)}m`;
}

export function ResolutionHeader({ result, className }: ResolutionHeaderProps) {
  const getStatusIcon = (status: string) => {
    if (status === "completed") return <CheckCircle className="h-5 w-5 text-status-complete" />;
    if (status === "rejected" || status === "failed") return <XCircle className="h-5 w-5 text-status-deny" />;
    if (status === "pending_approval") return <AlertCircle className="h-5 w-5 text-status-wait" />;
    return <Clock className="h-5 w-5 text-status-progress" />;
  };

  const duration = useMemo(() => formatDuration(result.created_at, result.completed_at), [result.created_at, result.completed_at]);

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className="p-4 border-b border-border-default bg-surface-base/50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="p-2 rounded-lg bg-status-evidence/10 text-status-evidence flex-shrink-0" aria-hidden="true">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-h1 font-semibold text-foreground truncate">Resolution</h2>
                <StatusBadge status={result.status as "pending" | "understanding" | "investigating" | "retrieving_policy" | "deciding" | "policy_check" | "pending_approval" | "executing" | "verifying" | "completed" | "rejected" | "failed"} size="md" />
              </div>
              <p className="text-body-sm text-muted-foreground mt-1 font-mono">{result.workflow_id}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 flex-wrap sm:justify-end">
            {result.order_number && (
              <div className="flex items-center gap-1.5 text-body-sm text-muted-foreground">
                <Hash className="h-3.5 w-3.5" aria-hidden="true" />
                <span className="font-mono">{result.order_number}</span>
              </div>
            )}
            {result.order_id && (
              <div className="flex items-center gap-1.5 text-body-sm text-muted-foreground">
                <Hash className="h-3.5 w-3.5" aria-hidden="true" />
                <span className="font-mono">ID: {result.order_id}</span>
              </div>
            )}
            {duration && (
              <div className="flex items-center gap-1.5 text-body-sm text-muted-foreground">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Duration: {duration}</span>
              </div>
            )}
            {result.created_at && (
              <div className="flex items-center gap-1.5 text-body-sm text-muted-foreground">
                <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                <span>{new Date(result.created_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-border-default">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Request ID</p>
              <p className="text-mono text-sm select-all">{result.request_id}</p>
            </div>
            <div className="space-y-1">
              <p className="text-label text-muted-foreground">Intent</p>
              <p className="text-body capitalize">{result.intent.replace(/_/g, " ")}</p>
            </div>
            {result.customer_id && (
              <div className="space-y-1">
                <p className="text-label text-muted-foreground">Customer</p>
                <div className="flex items-center gap-1.5 text-body-sm">
                  <User className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
                  <span className="font-mono">{result.customer_id}</span>
                </div>
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="space-y-1">
                <p className="text-label text-status-deny flex items-center gap-1">
                  <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                  Errors: {result.errors.length}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 bg-muted/30 border-t border-border-default">
        <p className="text-label text-muted-foreground mb-1">Customer Request</p>
        <p className="text-body whitespace-pre-wrap text-foreground">{result.user_request || "No request text available"}</p>
        {result.errors.length > 0 && (
          <div className="mt-2 p-2 rounded bg-status-deny/5 border border-status-deny/20">
            <p className="text-body-sm text-status-deny font-medium">{result.status === "failed" ? "Request failed" : "Status"}:</p>
            <p className="text-body-sm text-status-deny">{result.errors.join(", ")}</p>
          </div>
        )}
      </div>
    </div>
  );
}