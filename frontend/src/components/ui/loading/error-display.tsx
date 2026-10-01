"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { RefreshCw, AlertTriangle } from "lucide-react";

interface ErrorDisplayProps {
  error: Error | string | null;
  onRetry?: () => void;
  fallbackMessage?: string;
}

export function ErrorDisplay({
  error,
  onRetry,
  fallbackMessage = "An unexpected error occurred",
}: ErrorDisplayProps) {
  const message = error instanceof Error ? error.message : error || fallbackMessage;

  return (
    <Alert variant="destructive" className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-5 w-5" />
        <AlertTitle>Error</AlertTitle>
      </div>
      <AlertDescription className="text-sm">{message}</AlertDescription>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      )}
    </Alert>
  );
}

interface InlineErrorProps {
  message: string;
  onDismiss?: () => void;
}

export function InlineError({ message, onDismiss }: InlineErrorProps) {
  return (
    <Alert variant="destructive" className="flex items-center justify-between">
      <AlertDescription className="flex-1 text-sm">{message}</AlertDescription>
      {onDismiss && (
        <Button variant="ghost" size="icon" onClick={onDismiss} className="h-8 w-8">
          <span className="sr-only">Dismiss</span>
          ✕
        </Button>
      )}
    </Alert>
  );
}