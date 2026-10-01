"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, RefreshCw, CheckCircle, XCircle, BarChart2 } from "lucide-react";
import { useRefresh } from "@/lib/refresh-context";

interface EvaluationSummary {
  total_scenarios: number;
  passed: number;
  failed: number;
  skipped: number;
  by_category: Record<string, { passed: number; failed: number; skipped: number }>;
  total_duration_ms: number;
  timestamp: string;
  results: EvaluationResult[];
}

interface EvaluationResult {
  scenario_id: string;
  scenario_name: string;
  status: "PASS" | "FAIL" | "SKIPPED";
  duration_ms: number;
  checks_passed: string[];
  checks_failed: string[];
  skip_reason?: string;
  failure_reason?: string;
}

async function fetchEvaluationResults(): Promise<EvaluationSummary | null> {
  try {
    const data = await apiClient.getEvaluationResults();
    return data;
  } catch {
    return null;
  }
}

function StatusBadge({ status }: { status: "PASS" | "FAIL" | "SKIPPED" }) {
  const statusConfig = {
    PASS: { icon: CheckCircle, className: "bg-green-100 text-green-800" },
    FAIL: { icon: XCircle, className: "bg-red-100 text-red-800" },
    SKIPPED: { icon: AlertTriangle, className: "bg-yellow-100 text-yellow-800" },
  };
  const config = statusConfig[status];
  const Icon = config.icon;
  return (
    <Badge className={`${config.className} gap-1`} variant="default">
      <Icon className="h-3 w-3" />
      {status}
    </Badge>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold">{value}</p>
          </div>
          <div className="text-primary">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function EvaluationSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardContent className="p-6">
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-red-500/50" />
        <h3 className="text-lg font-medium mb-2">Failed to load evaluation results</h3>
        <p className="text-muted-foreground mb-6">
          The backend may not be running or the evaluation endpoint is unavailable.
        </p>
        <Button onClick={onRetry} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      </CardContent>
    </Card>
  );
}

export default function EvaluationPage() {
  const [queryError, setQueryError] = useState(false);
  const { setRefreshFn } = useRefresh();

  const { data, isLoading, error, refetch } = useQuery<EvaluationSummary | null>({
    queryKey: ["evaluation"],
    queryFn: async () => {
      setQueryError(false);
      try {
        return await fetchEvaluationResults();
      } catch {
        setQueryError(true);
        return null;
      }
    },
    enabled: true,
    refetchInterval: false,
  });
  useEffect(() => { setRefreshFn(refetch); return () => setRefreshFn(null); }, [refetch, setRefreshFn]);

  const isError = queryError || error || (data === null && !isLoading);
  const hasData = data !== null && !isLoading && !isError;
  const isEmpty = hasData && data && data.total_scenarios === 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <BarChart2 className="h-8 w-8" />
            Evaluation Results
          </h1>
          <p className="text-muted-foreground">
            End-to-end benchmark of the resolution workflow against real backend, database and LLM
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {isLoading && <EvaluationSkeleton />}

      {isError && !isLoading && <ErrorState onRetry={() => refetch()} />}

      {hasData && data && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard label="Total Scenarios" value={data.total_scenarios} icon={<BarChart2 className="h-8 w-8" />} />
            <MetricCard label="Passed" value={data.passed} icon={<CheckCircle className="h-8 w-8 text-green-600" />} />
            <MetricCard label="Failed" value={data.failed} icon={<XCircle className="h-8 w-8 text-red-600" />} />
            <MetricCard label="Skipped" value={data.skipped} icon={<AlertTriangle className="h-8 w-8 text-yellow-600" />} />
          </div>

          {data.timestamp && (
            <p className="text-sm text-muted-foreground">
              Last run: {data.timestamp} · Total duration: {data.total_duration_ms}ms · Pass rate:{" "}
              {data.total_scenarios > 0 ? ((data.passed / data.total_scenarios) * 100).toFixed(1) : 0}%
            </p>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Results by Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-center">Passed</TableHead>
                      <TableHead className="text-center">Failed</TableHead>
                      <TableHead className="text-center">Skipped</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(data.by_category).map(([category, counts]) => (
                      <TableRow key={category}>
                        <TableCell className="font-medium capitalize">{category}</TableCell>
                        <TableCell className="text-center text-green-600 font-medium">{counts.passed}</TableCell>
                        <TableCell className="text-center text-red-600 font-medium">{counts.failed}</TableCell>
                        <TableCell className="text-center text-yellow-600 font-medium">{counts.skipped}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Detailed Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Scenario</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Failure Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.results.map((result) => (
                      <TableRow key={result.scenario_id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{result.scenario_name}</p>
                            <p className="text-sm text-muted-foreground">{result.scenario_id}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={result.status} />
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{result.duration_ms}ms</TableCell>
                        <TableCell className="text-sm">
                          {result.failure_reason || result.skip_reason || "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {isEmpty && (
        <Card>
          <CardContent className="py-12 text-center">
            <BarChart2 className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
            <h3 className="text-lg font-medium mb-2">No evaluation results yet</h3>
            <p className="text-muted-foreground mb-6">
              Run the real integration evaluation to see results here.
            </p>
            <div className="space-y-3 max-w-md mx-auto text-left">
              <code className="block px-4 py-2 bg-muted rounded font-mono text-sm">
                cd backend && python -m evaluation.integration.real_runner
              </code>
              <p className="text-sm text-muted-foreground">
                Requires SUPABASE_URL, SUPABASE_SERVICE_KEY, and GEMINI_API_KEY configured
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
