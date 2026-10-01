"use client";

import {
  useState,
  useCallback,
  useEffect,
  useRef,
  useTransition,
} from "react";
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
  Menu,
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

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const mobileNavPanelRef = useRef<HTMLDivElement>(null);
  const hamburgerRef = useRef<HTMLButtonElement>(null);

  const isActivePath = useCallback(
    (href: string) =>
      pathname === href || (href !== "/" && pathname.startsWith(href)),
    [pathname]
  );

  const closeMobileNav = useCallback(() => {
    setMobileNavOpen(false);
  }, []);

  // Close the menu whenever navigation happens (link tap or browser back/forward).
  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  // Scroll lock + move focus into the menu, and restore focus to the
  // hamburger on close so keyboard users never lose their place.
  useEffect(() => {
    if (!mobileNavOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const focusables = () =>
      Array.from(
        mobileNavPanelRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        ) ?? []
      );

    focusables()[0]?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      hamburgerRef.current?.focus();
    };
  }, [mobileNavOpen]);

  // Escape closes, Tab is trapped inside the open menu, and a tap on the
  // backdrop (outside the panel) closes.
  useEffect(() => {
    if (!mobileNavOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobileNavOpen(false);
        return;
      }

      if (event.key !== "Tab") return;

      const focusables = Array.from(
        mobileNavPanelRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        ) ?? []
      );
      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;

      if (event.shiftKey && (active === first || !mobileNavPanelRef.current?.contains(active))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target as Node | null;
      if (!target) return;
      if (mobileNavPanelRef.current?.contains(target)) return;
      setMobileNavOpen(false);
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("pointerdown", handlePointerDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [mobileNavOpen]);

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
              const isActive = isActivePath(item.href);
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
            ref={hamburgerRef}
            variant="ghost"
            size="icon"
            className="h-9 w-9 md:hidden"
            onClick={() => setMobileNavOpen((open) => !open)}
            aria-expanded={mobileNavOpen}
            aria-controls="mobile-navigation-menu"
            aria-label={mobileNavOpen ? "Close navigation menu" : "Open navigation menu"}
            title="Menu"
          >
            {mobileNavOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
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

      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Close navigation menu"
            tabIndex={-1}
            onClick={closeMobileNav}
            className="absolute inset-0 h-full w-full cursor-default bg-black/50"
          />
          <div
            id="mobile-navigation-menu"
            ref={mobileNavPanelRef}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
            className="absolute inset-x-0 top-0 max-h-[100dvh] overflow-y-auto border-b bg-background shadow-lg"
          >
            <div className="flex h-16 items-center justify-between border-b px-4">
              <span className="font-bold text-lg">Menu</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9"
                onClick={closeMobileNav}
                aria-label="Close navigation menu"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="flex flex-col gap-1 p-3">
              {navigation.map((item) => {
                const isActive = isActivePath(item.href);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={closeMobileNav}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "flex min-h-11 items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}

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
