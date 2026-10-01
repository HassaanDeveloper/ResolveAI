"use client";

import { useState, useCallback, useTransition } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  FileText,
  ClipboardList,
  BookOpen,
  BarChart2,
  Settings,
  RefreshCw,
  Loader2,
  X,
} from "lucide-react";
import { useRefresh } from "@/lib/refresh-context";
import { apiClient } from "@/lib/api";
import type { HealthResponse } from "@/types/api";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Resolution Console", href: "/console", icon: FileText },
  { name: "Approval Queue", href: "/approvals", icon: ClipboardList },
  { name: "Knowledge Base", href: "/knowledge", icon: BookOpen },
  { name: "Evaluation", href: "/evaluation", icon: BarChart2 },
];

export function Navigation() {
  const pathname = usePathname();
  const { refreshFn } = useRefresh();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState(false);
  const [isPending, startTransition] = useTransition();

  const handleRefresh = useCallback(() => {
    if (refreshFn) {
      startTransition(() => {
        refreshFn();
      });
    }
  }, [refreshFn]);

  const handleSettingsOpen = useCallback(() => {
    setSettingsOpen(true);
    setHealthLoading(true);
    setHealthError(false);
    apiClient.healthCheck().then(
      (data) => { setHealthData(data); setHealthLoading(false); },
      () => { setHealthError(true); setHealthLoading(false); }
    );
  }, []);

  const handleSettingsClose = useCallback(() => {
    setSettingsOpen(false);
  }, []);

  return (
    <>
      <nav className="flex h-16 items-center gap-1 border-b bg-background px-4">
        <div className="flex items-center gap-6 flex-1">
          <Link href="/" className="font-bold text-lg">
            ResolveAI
          </Link>
          <div className="hidden md:flex items-center gap-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9"
            onClick={handleRefresh}
            disabled={isPending}
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isPending ? "animate-spin" : ""}`} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9"
            onClick={handleSettingsOpen}
            title="Settings"
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </nav>

      {settingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card rounded-lg border shadow-lg w-96 max-w-[90vw] p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Settings</h2>
              <Button variant="ghost" size="icon" onClick={handleSettingsClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-3">
              {healthLoading && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Checking backend status...
                </div>
              )}
              {healthError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  Failed to connect to backend
                </div>
              )}
              {healthData && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <span className="text-sm font-medium">{healthData.status}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <span className="text-sm text-muted-foreground">Application</span>
                    <span className="text-sm font-medium">{healthData.application}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <span className="text-sm text-muted-foreground">Environment</span>
                    <span className="text-sm font-medium">{healthData.environment}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
