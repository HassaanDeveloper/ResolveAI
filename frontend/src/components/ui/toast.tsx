"use client";

import * as React from "react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { X, CheckCircle, AlertTriangle, Info, Loader2 } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info" | "loading";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => string;
  removeToast: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

const typeConfig: Record<ToastType, { icon: React.ElementType; variant: string }> = {
  success: { icon: CheckCircle, variant: "bg-status-complete text-status-complete-foreground" },
  error: { icon: AlertTriangle, variant: "bg-status-deny text-status-deny-foreground" },
  warning: { icon: AlertTriangle, variant: "bg-status-wait text-status-wait-foreground" },
  info: { icon: Info, variant: "bg-status-progress text-status-progress-foreground" },
  loading: { icon: Loader2, variant: "bg-status-progress text-status-progress-foreground" },
};

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const { icon: Icon, variant } = typeConfig[toast.type];
  const isLoading = toast.type === "loading";

  React.useEffect(() => {
    if (toast.duration !== 0 && !isLoading) {
      const timer = setTimeout(() => onRemove(toast.id), toast.duration ?? 5000);
      return () => clearTimeout(timer);
    }
  }, [toast, onRemove, isLoading]);

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border shadow-lg",
        "animate-in slide-in-from-top-right fade-in duration-150",
        "data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=closed]:fade-out",
        variant,
        toast.type === "loading" && "animate-pulse",
      )}
      role="alert"
      aria-live={toast.type === "error" ? "assertive" : "polite"}
    >
      <div className="shrink-0 mt-0.5" aria-hidden="true">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-body font-medium">{toast.title}</p>
        {toast.description && (
          <p className="text-body-sm opacity-90 mt-1">{toast.description}</p>
        )}
      </div>
      {toast.action && (
        <Button
          variant="ghost"
          size="sm"
          className="text-current opacity-70 hover:opacity-100"
          onClick={() => {
            toast.action?.onClick();
            onRemove(toast.id);
          }}
        >
          {toast.action.label}
        </Button>
      )}
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-current opacity-50 hover:opacity-100 shrink-0"
        onClick={() => onRemove(toast.id)}
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const addToast = React.useCallback((toast: Omit<Toast, "id">) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...toast, id }]);
    return id;
  }, []);

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <div
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-full"
        aria-live="polite"
        aria-label="Notifications"
      >
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

export function toast({
  type,
  title,
  description,
  duration,
  action,
}: Omit<Toast, "id">) {
  return { type, title, description, duration, action };
}