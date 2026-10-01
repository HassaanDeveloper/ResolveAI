"use client";

import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SkeletonTable } from "@/components/ui/loading/skeleton-card";
import { apiClient } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { DashboardMetrics } from "@/types/api";
import { Button } from "@/components/ui/button";
import { useRefresh } from "@/lib/refresh-context";
import {
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  BookOpen,
  ArrowRight,
} from "lucide-react";

function MetricCard({
  label,
  value,
  icon,
  borderColor = "border-l-blue-500",
  iconBg = "bg-blue-100 text-blue-600",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  borderColor?: string;
  iconBg?: string;
}) {
  return (
    <Card className={`border border-l-4 overflow-hidden transition-shadow hover:shadow-md ${borderColor}`}>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold tracking-tight">{value}</p>
          </div>
          <div className={`${iconBg} p-3 rounded-lg`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () => apiClient.getDashboardMetrics(),
    refetchInterval: 30000,
  });
  const { setRefreshFn } = useRefresh();
  useEffect(() => { setRefreshFn(refetch); return () => setRefreshFn(null); }, [refetch, setRefreshFn]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of ResolveAI business resolution engine
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card><CardContent className="pt-6"><SkeletonTable rows={1} /></CardContent></Card>
          <Card><CardContent className="pt-6"><SkeletonTable rows={1} /></CardContent></Card>
          <Card><CardContent className="pt-6"><SkeletonTable rows={1} /></CardContent></Card>
          <Card><CardContent className="pt-6"><SkeletonTable rows={1} /></CardContent></Card>
          <Card><CardContent className="pt-6"><SkeletonTable rows={1} /></CardContent></Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of ResolveAI business resolution engine
          </p>
        </div>
        <Card className="border-red-200">
          <CardContent className="py-8 text-center text-red-600">
            Failed to load dashboard metrics. Please try again.
            <Button variant="outline" onClick={() => refetch()} className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const metrics = data as DashboardMetrics;

  const successRate = metrics.total_requests > 0
    ? ((metrics.successful_resolutions / metrics.total_requests) * 100).toFixed(0)
    : "0";
  const failureRate = metrics.total_requests > 0
    ? ((metrics.failed_resolutions / metrics.total_requests) * 100).toFixed(0)
    : "0";
  const avgTimeDisplay = metrics.avg_resolution_time_ms !== null && metrics.avg_resolution_time_ms !== undefined
    ? `${Math.round(metrics.avg_resolution_time_ms / 1000)}s`
    : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of ResolveAI business resolution engine
          </p>
        </div>
        <button onClick={() => refetch()} className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent transition-colors">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Real computed headline stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="surface-elevated rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle className="h-4 w-4 text-status-complete" aria-hidden="true" />
            <span className="text-label font-semibold tracking-wider text-muted-foreground">SUCCESS RATE</span>
          </div>
          <p className="text-2xl font-bold text-foreground">{successRate}%</p>
          <p className="text-xs text-muted-foreground mt-1">of requests completed successfully</p>
        </div>
        <div className="surface-elevated rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <XCircle className="h-4 w-4 text-status-deny" aria-hidden="true" />
            <span className="text-label font-semibold tracking-wider text-muted-foreground">FAILURE RATE</span>
          </div>
          <p className="text-2xl font-bold text-foreground">{failureRate}%</p>
          <p className="text-xs text-muted-foreground mt-1">of requests resolved with failure</p>
        </div>
        <div className="surface-elevated rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-status-wait" aria-hidden="true" />
            <span className="text-label font-semibold tracking-wider text-muted-foreground">PENDING</span>
          </div>
          <p className="text-2xl font-bold text-foreground">{metrics.pending_approvals}</p>
          <p className="text-xs text-muted-foreground mt-1">actions awaiting attention</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          label="Total Requests"
          value={metrics?.total_requests || 0}
          icon={<FileText className="h-6 w-6 text-blue-600" />}
          borderColor="border-l-blue-500"
          iconBg="bg-blue-100 text-blue-600"
        />
        <MetricCard
          label="Successful Resolutions"
          value={metrics?.successful_resolutions || 0}
          icon={<CheckCircle className="h-6 w-6 text-status-complete" />}
          borderColor="border-l-emerald-500"
          iconBg="bg-emerald-100 text-emerald-600"
        />
        <MetricCard
          label="Pending Approvals"
          value={metrics?.pending_approvals || 0}
          icon={<Clock className="h-6 w-6 text-status-wait" />}
          borderColor="border-l-amber-500"
          iconBg="bg-amber-100 text-amber-600"
        />
        <MetricCard
          label="Failed Resolutions"
          value={metrics?.failed_resolutions || 0}
          icon={<XCircle className="h-6 w-6 text-status-deny" />}
          borderColor="border-l-red-500"
          iconBg="bg-red-100 text-red-600"
        />
        <MetricCard
          label="Avg Resolution Time"
          value={avgTimeDisplay || "Not enough data"}
          icon={<Clock className="h-6 w-6 text-purple-600" />}
          borderColor="border-l-purple-500"
          iconBg="bg-purple-100 text-purple-600"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <a
            href="/console"
            className="block p-4 rounded-lg hover:bg-accent hover:shadow-sm transition-all duration-200 text-center surface-card"
          >
            <FileText className="h-8 w-8 mx-auto mb-2 text-muted-foreground" aria-hidden="true" />
            <p className="font-medium">Resolution Console</p>
            <p className="text-sm text-muted-foreground">
              Submit and track resolution requests
            </p>
            <ArrowRight className="h-4 w-4 mx-auto mt-2 text-muted-foreground" aria-hidden="true" />
          </a>
          <a
            href="/approvals"
            className="block p-4 rounded-lg hover:bg-accent hover:shadow-sm transition-all duration-200 text-center surface-card"
          >
            <Clock className="h-8 w-8 mx-auto mb-2 text-muted-foreground" aria-hidden="true" />
            <p className="font-medium">Approval Queue</p>
            <p className="text-sm text-muted-foreground">
              Review pending approvals
            </p>
            <ArrowRight className="h-4 w-4 mx-auto mt-2 text-muted-foreground" aria-hidden="true" />
          </a>
          <a
            href="/knowledge"
            className="block p-4 rounded-lg hover:bg-accent hover:shadow-sm transition-all duration-200 text-center surface-card"
          >
            <BookOpen className="h-8 w-8 mx-auto mb-2 text-muted-foreground" aria-hidden="true" />
            <p className="font-medium">Knowledge Base</p>
            <p className="text-sm text-muted-foreground">
              Browse company policies
            </p>
            <ArrowRight className="h-4 w-4 mx-auto mt-2 text-muted-foreground" aria-hidden="true" />
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
