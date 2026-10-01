"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { useRefresh } from "@/lib/refresh-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ClipboardList, Filter, Eye, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SkeletonTable } from "@/components/ui/loading/skeleton-card";
import { apiClient } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ApprovalListItem, ApprovalStatus } from "@/types/api";
import { LoadingButton } from "@/components/ui/loading/loading-spinner";
import { ErrorDisplay } from "@/components/ui/loading/error-display";
import { StatusBadge } from "@/components/ui/status-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { EmptyState } from "@/components/ui/empty-state";

async function fetchApprovals(status?: string) {
  return apiClient.listApprovals(status);
}

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "executed", label: "Executed" },
  { value: "failed", label: "Failed" },
];

export default function ApprovalsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState<string>("");
  const { setRefreshFn } = useRefresh();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["approvals", filterStatus],
    queryFn: () => fetchApprovals(filterStatus || undefined),
  });
  useEffect(() => { setRefreshFn(refetch); return () => setRefreshFn(null); }, [refetch, setRefreshFn]);

  const decideMutation = useMutation({
    mutationFn: ({ approvalId, decision, reason }: { approvalId: string; decision: "approved" | "rejected"; reason?: string }) =>
      apiClient.decideApproval(approvalId, {
        approval_id: approvalId,
        decision,
        decided_by: "human_operator",
        reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals", filterStatus] });
    },
    onError: (err: Error) => {
      alert(`Failed to process decision: ${err.message}`);
    },
  });

  const handleApprove = (approvalId: string) => {
    decideMutation.mutate({ approvalId, decision: "approved" });
  };

  const handleReject = (approvalId: string) => {
    const reason = prompt("Please provide a reason for rejection:");
    if (reason) {
      decideMutation.mutate({ approvalId, decision: "rejected", reason });
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <ClipboardList className="h-8 w-8" />
            Approval Queue
          </h1>
        </div>
        <Card>
          <CardContent>
            <SkeletonTable rows={10} />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <Card className="border-red-200">
          <CardContent className="py-8 text-center text-red-600">
            Failed to load approvals. Please try again.
            <Button variant="outline" onClick={() => refetch()} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const approvals = data?.approvals || [];

  const pendingApprovals = approvals.filter((a) => a.status === "pending");

  const approvalFields = (approval: ApprovalListItem) => (
    <dl className="grid grid-cols-[minmax(0,7rem)_minmax(0,1fr)] gap-x-3 gap-y-2">
      <dt className="text-label">ID</dt>
      <dd className="text-mono text-body-sm break-all">{approval.id}</dd>
      <dt className="text-label">Resolution</dt>
      <dd className="text-mono text-body-sm break-all">{approval.resolution_id}</dd>
      <dt className="text-label">Action</dt>
      <dd className="text-body-sm capitalize">
        {approval.action_type.replace(/_/g, " ")}
      </dd>
      <dt className="text-label">Reason</dt>
      <dd className="text-body-sm break-words">{approval.reason}</dd>
      <dt className="text-label">Risk Level</dt>
      <dd>
        <RiskBadge
          level={approval.risk_level as "LOW" | "MEDIUM" | "HIGH"}
          size="sm"
        />
      </dd>
      <dt className="text-label">Status</dt>
      <dd>
        <StatusBadge status={approval.status} size="sm" />
      </dd>
      <dt className="text-label">Requested</dt>
      <dd className="text-mono text-body-sm text-muted-foreground">
        {format(new Date(approval.requested_at), "PPp")}
      </dd>
    </dl>
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-display font-bold tracking-tight flex items-center gap-2">
            <ClipboardList className="h-8 w-8" />
            Approval Queue
          </h1>
          <p className="text-body text-muted-foreground mt-1">
            Review and decide on pending high-risk actions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={filterStatus} onValueChange={(value) => setFilterStatus(value || "")}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            Pending Approvals ({approvals.filter((a) => a.status === "pending").length})
          </CardTitle>
        </CardHeader>
<CardContent>
          {/* Mobile: stacked cards, one per approval, actions pinned to the bottom. */}
          <div className="flex flex-col gap-3 md:hidden">
            {approvals.length === 0 ? (
              <EmptyState
                title="No approvals found"
                description={
                  filterStatus
                    ? `No approvals with status "${filterStatus}"`
                    : "No pending approvals at this time."
                }
                icon={<ClipboardList />}
              />
            ) : (
              pendingApprovals.map((approval) => (
                <div
                  key={approval.id}
                  className="flex flex-col gap-3 rounded-lg border bg-card p-4"
                >
                  {approvalFields(approval)}
                  <div className="flex flex-col gap-2 border-t pt-3 sm:flex-row sm:flex-wrap">
                    <Button
                      variant="outline"
                      size="sm"
                      className="min-h-11 w-full sm:w-auto"
                      onClick={() => router.push(`/approvals/${approval.id}`)}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      View Detail
                    </Button>
                    <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
                      <LoadingButton
                        isLoading={decideMutation.isPending}
                        onClick={() => handleApprove(approval.id)}
                        variant="default"
                        size="sm"
                        className="min-h-11 w-full"
                      >
                        Approve
                      </LoadingButton>
                      <LoadingButton
                        isLoading={decideMutation.isPending}
                        onClick={() => handleReject(approval.id)}
                        variant="destructive"
                        size="sm"
                        className="min-h-11 w-full"
                      >
                        Reject
                      </LoadingButton>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Desktop: fixed-column table. */}
          <div className="hidden overflow-x-auto md:block">
            <Table style={{ tableLayout: "fixed" }}>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-label">ID</TableHead>
                  <TableHead className="text-label">Resolution ID</TableHead>
                  <TableHead className="text-label">Action</TableHead>
                  <TableHead className="text-label">Reason</TableHead>
                  <TableHead className="text-label">Risk Level</TableHead>
                  <TableHead className="text-label">Status</TableHead>
                  <TableHead className="text-label">Requested At</TableHead>
                  <TableHead className="text-label w-60">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-8">
                      <EmptyState
                        title="No approvals found"
                        description={filterStatus ? `No approvals with status "${filterStatus}"` : "No pending approvals at this time."}
                        icon={<ClipboardList />}
                      />
                    </TableCell>
                  </TableRow>
                ) : (
                  approvals.map((approval) => (
                    <TableRow key={approval.id}>
                      <TableCell className="text-mono truncate">{approval.id.slice(0, 8)}...</TableCell>
                      <TableCell className="text-mono truncate">{approval.resolution_id.slice(0, 8)}...</TableCell>
                      <TableCell className="text-body capitalize truncate">{approval.action_type.replace("_", " ")}</TableCell>
                      <TableCell className="max-w-xs truncate text-body-sm">{approval.reason}</TableCell>
                      <TableCell>
                        <RiskBadge level={approval.risk_level as "LOW" | "MEDIUM" | "HIGH"} size="sm" />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={approval.status} size="sm" />
                      </TableCell>
                      <TableCell className="text-mono text-muted-foreground truncate">
                        {format(new Date(approval.requested_at), "PPp")}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => router.push(`/approvals/${approval.id}`)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {approval.status === "pending" && (
                            <>
                              <LoadingButton
                                isLoading={decideMutation.isPending}
                                onClick={() => handleApprove(approval.id)}
                                variant="default"
                                size="sm"
                                className="h-8"
                              >
                                Approve
                              </LoadingButton>
                              <LoadingButton
                                isLoading={decideMutation.isPending}
                                onClick={() => handleReject(approval.id)}
                                variant="destructive"
                                size="sm"
                                className="h-8"
                              >
                                Reject
                              </LoadingButton>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
       </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Approvals ({approvals.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Mobile: stacked cards, one per approval. */}
          <div className="flex flex-col gap-3 md:hidden">
            {approvals.length === 0 ? (
              <EmptyState
                title="No approvals found"
                description="No approvals have been recorded yet."
                icon={<ClipboardList />}
              />
            ) : (
              approvals.map((approval) => (
                <div
                  key={approval.id}
                  className="flex flex-col gap-3 rounded-lg border bg-card p-4"
                >
                  {approvalFields(approval)}
                  {approval.status === "pending" ? (
                    <div className="flex flex-col gap-3 border-t pt-3 sm:flex-row sm:flex-wrap">
                      <Button
                        variant="outline"
                        size="sm"
                        className="min-h-11 w-full sm:w-auto"
                        onClick={() => router.push(`/approvals/${approval.id}`)}
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        View Detail
                      </Button>
                      <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
                        <LoadingButton
                          isLoading={decideMutation.isPending}
                          onClick={() => handleApprove(approval.id)}
                          variant="default"
                          size="sm"
                          className="min-h-11 w-full"
                        >
                          Approve
                        </LoadingButton>
                        <LoadingButton
                          isLoading={decideMutation.isPending}
                          onClick={() => handleReject(approval.id)}
                          variant="destructive"
                          size="sm"
                          className="min-h-11 w-full"
                        >
                          Reject
                        </LoadingButton>
                      </div>
                    </div>
                  ) : (
                    <div className="border-t pt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        className="min-h-11 w-full sm:w-auto"
                        onClick={() => router.push(`/approvals/${approval.id}`)}
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        View Detail
                      </Button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Desktop: fixed-column table. */}
          <div className="hidden overflow-x-auto md:block">
            <Table style={{ tableLayout: "fixed" }}>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-label">ID</TableHead>
                  <TableHead className="text-label">Resolution ID</TableHead>
                  <TableHead className="text-label">Action</TableHead>
                  <TableHead className="text-label">Reason</TableHead>
                  <TableHead className="text-label">Risk Level</TableHead>
                  <TableHead className="text-label">Status</TableHead>
                  <TableHead className="text-label">Requested At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8">
                      <EmptyState
                        title="No approvals found"
                        description="No approvals have been recorded yet."
                        icon={<ClipboardList />}
                      />
                    </TableCell>
                  </TableRow>
                ) : (
                  approvals.map((approval) => (
                    <TableRow key={approval.id}>
                      <TableCell className="text-mono truncate">{approval.id.slice(0, 8)}...</TableCell>
                      <TableCell className="text-mono truncate">{approval.resolution_id.slice(0, 8)}...</TableCell>
                      <TableCell className="text-body capitalize truncate">{approval.action_type.replace("_", " ")}</TableCell>
                      <TableCell className="max-w-xs truncate text-body-sm">{approval.reason}</TableCell>
                      <TableCell>
                        <RiskBadge level={approval.risk_level as "LOW" | "MEDIUM" | "HIGH"} size="sm" />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={approval.status} size="sm" />
                      </TableCell>
                      <TableCell className="text-mono text-muted-foreground truncate">
                        {format(new Date(approval.requested_at), "PPp")}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}