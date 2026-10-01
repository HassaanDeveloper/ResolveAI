"use client";

import { cn } from "cn";
import { ClipboardCheck, XCircle, AlertTriangle, CheckCircle, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import * as React from "react";

interface VerificationRecord {
  success: boolean;
  verified_at: string;
  details: Record<string, unknown>;
  error?: string;
}

interface VerificationSectionProps {
  verification?: VerificationRecord;
  actionTaken?: string;
  className?: string;
}

export function VerificationSection({ verification, actionTaken, className }: VerificationSectionProps) {
  const [showDetails, setShowDetails] = React.useState(false);

  if (!verification) {
    return (
      <div className={cn("border border-border-default rounded-lg bg-surface-card p-4", className)}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-muted/50 text-muted-foreground" aria-hidden="true">
            <ClipboardCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-h2 font-medium text-foreground">Verification Pending</p>
            <p className="text-body-sm text-muted-foreground">
              The action has not yet been verified. Verification typically occurs after execution completes.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const actionLabel = actionTaken?.replace(/_/g, " ") || "Action";

  return (
    <div className={cn("border border-border-default rounded-lg bg-surface-card overflow-hidden", className)}>
      <div className={cn(
        "px-4 py-3 flex items-center gap-3 border-b border-border-default",
        verification.success ? "bg-status-complete/5" : "bg-status-deny/5",
      )}>
        <div className={cn(
          "p-2 rounded-lg flex-shrink-0",
          verification.success ? "bg-status-complete/10 text-status-complete" : "bg-status-deny/10 text-status-deny",
        )} aria-hidden="true">
          {verification.success ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
        </div>
        <div className="flex-1">
          <p className="text-h2 font-medium text-foreground">
            {verification.success ? "Verification Successful" : "Verification Failed"}
          </p>
          <p className="text-body-sm text-muted-foreground">
            {verification.success
              ? `The ${actionLabel.toLowerCase()} was confirmed to have completed successfully.`
              : `The ${actionLabel.toLowerCase()} could not be verified. Manual investigation may be required.`}
          </p>
        </div>
        <StatusBadge status={verification.success ? "completed" : "failed"} size="md" />
      </div>

      <div className="p-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Verified At</p>
            <p className="text-mono">{verification.verified_at ? new Date(verification.verified_at).toLocaleString() : "—"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-label text-muted-foreground">Action Verified</p>
            <p className="text-body capitalize">{actionLabel}</p>
          </div>
        </div>

        {verification.details && Object.keys(verification.details).length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-label text-muted-foreground">Verification Details</p>
              <button
                type="button"
                className="flex items-center gap-1 text-body-sm text-primary hover:text-primary/80"
                onClick={() => setShowDetails(!showDetails)}
                aria-expanded={showDetails}
              >
                {showDetails ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                {showDetails ? "Hide" : "Show"}
              </button>
            </div>
            <div
              className={cn("overflow-hidden transition-all duration-150", showDetails ? "max-h-96 opacity-100" : "max-h-0 opacity-0")}
            >
              <div className="p-3 bg-muted/50 rounded border border-border-default">
                <pre className="text-code overflow-x-auto"><code>{JSON.stringify(verification.details, null, 2)}</code></pre>
              </div>
            </div>
          </div>
        )}

        {verification.error && (
          <div className="space-y-2 pt-2 border-t border-border-default">
            <p className="text-label text-status-deny flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" aria-hidden="true" />
              Verification Error
            </p>
            <p className="text-body-sm text-status-deny font-mono bg-status-deny/5 p-3 rounded">{verification.error}</p>
            <p className="text-body-sm text-muted-foreground">
              The verification process encountered an error. This does not necessarily mean the action failed—
              manual confirmation may be needed.
            </p>
          </div>
        )}

        <div className="pt-2 border-t border-border-default">
          <div className="p-3 rounded-lg bg-status-complete/5 border border-status-complete/20">
            <div className="flex items-start gap-2">
              <ClipboardCheck className="h-4 w-4 text-status-complete flex-shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <p className="text-body-sm font-medium text-foreground">Execution vs. Verification</p>
                <p className="text-body-sm text-muted-foreground mt-0.5">
                  <strong>Execution</strong> performs the authorized business action (e.g., issuing a refund).
                  <strong>Verification</strong> independently confirms the action actually took effect in the target system.
                  Both must succeed for a resolution to be considered complete.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}