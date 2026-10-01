"use client";

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function LoadingSpinner({ size = "md", className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-10 w-10",
  };

  return (
    <Loader2
      className={cn(
        "animate-spin text-primary",
        sizeClasses[size],
        className
      )}
    />
  );
}

interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  children: React.ReactNode;
}

export function LoadingOverlay({
  isLoading,
  message = "Loading...",
  children,
}: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-10">
          <div className="bg-card p-6 rounded-lg shadow-lg flex flex-col items-center gap-3">
            <LoadingSpinner size="lg" />
            <p className="text-sm text-muted-foreground">{message}</p>
          </div>
        </div>
      )}
    </div>
  );
}

interface LoadingButtonProps {
  isLoading: boolean;
  children: React.ReactNode;
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  size?: "default" | "sm" | "lg" | "icon";
  type?: "button" | "submit" | "reset";
}

export function LoadingButton({
  isLoading,
  children,
  variant = "default",
  className,
  onClick,
  disabled,
  size = "default",
  type = "button",
}: LoadingButtonProps) {
  return (
    <Button
      variant={variant}
      className={cn("relative", className)}
      onClick={onClick}
      disabled={isLoading || disabled}
      size={size}
      type={type}
    >
      {isLoading ? (
        <>
          <LoadingSpinner size="sm" className="mr-2" />
          <span>Loading...</span>
        </>
      ) : (
        children
      )}
    </Button>
  );
}