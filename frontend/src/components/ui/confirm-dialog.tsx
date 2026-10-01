"use client";

import * as React from "react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { X } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  consequence?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "destructive";
  requireReason?: boolean;
  reasonPlaceholder?: string;
  reasonLabel?: string;
  onConfirm: (reason?: string) => void;
  isLoading?: boolean;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  consequence,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "default",
  requireReason = false,
  reasonPlaceholder,
  reasonLabel = "Reason",
  onConfirm,
  isLoading = false,
}: ConfirmDialogProps) {
  const [reason, setReason] = React.useState("");
  const [reasonError, setReasonError] = React.useState(false);
  const dialogRef = React.useRef<HTMLDivElement>(null);
  const previousFocusRef = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      dialogRef.current?.focus();
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
      previousFocusRef.current?.focus();
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  React.useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onOpenChange(false);
      }
      if (e.key === "Tab") {
        const focusableElements = dialogRef.current?.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusableElements && focusableElements.length > 0) {
          const first = focusableElements[0];
          const last = focusableElements[focusableElements.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  const handleConfirm = () => {
    if (requireReason && !reason.trim()) {
      setReasonError(true);
      return;
    }
    setReasonError(false);
    onConfirm(requireReason ? reason.trim() : undefined);
    onOpenChange(false);
  };

  const handleCancel = () => {
    setReason("");
    setReasonError(false);
    onOpenChange(false);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <div
        ref={dialogRef}
        tabIndex={-1}
        className={cn(
          "w-full max-w-md bg-surface-card border border-border-default rounded-lg shadow-lg",
          "animate-in fade-in zoom-in-95 duration-150",
          "data-[state=closed]:animate-out data-[state=closed]:fade-out data-[state=closed]:zoom-out-95",
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between p-4 border-b border-border-default">
          <div className="flex-1 pr-4">
            <h2
              id="confirm-dialog-title"
              className="text-h2 font-semibold text-foreground"
            >
              {title}
            </h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={handleCancel}
            aria-label="Close dialog"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-4 space-y-4">
          {description && (
            <p id="confirm-dialog-description" className="text-body text-muted-foreground">
              {description}
            </p>
          )}

          {consequence && (
            <div
              className="p-3 bg-status-wait/10 border border-status-wait/30 rounded-md"
              role="alert"
            >
              <p className="text-body-sm text-status-wait-foreground font-medium">
                {consequence}
              </p>
            </div>
          )}

          {requireReason && (
            <div className="space-y-2">
              <Label htmlFor="confirm-reason" className="text-label text-foreground">
                {reasonLabel}
              </Label>
              <Textarea
                id="confirm-reason"
                placeholder={reasonPlaceholder || "Enter reason..."}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleConfirm();
                  }
                }}
                className={cn(
                  "min-h-[80px]",
                  reasonError && "border-destructive focus-visible:ring-destructive",
                )}
                aria-invalid={reasonError}
                aria-describedby={reasonError ? "reason-error" : undefined}
              />
              {reasonError && (
                <p id="reason-error" className="text-body-sm text-destructive" role="alert">
                  A reason is required
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 p-4 border-t border-border-default bg-muted/30 rounded-b-lg">
          <Button
            variant="ghost"
            onClick={handleCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={variant}
            onClick={handleConfirm}
            disabled={isLoading}
            className={cn(
              variant === "destructive" && "bg-destructive hover:bg-destructive/90",
            )}
          >
            {isLoading ? "Confirming..." : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}