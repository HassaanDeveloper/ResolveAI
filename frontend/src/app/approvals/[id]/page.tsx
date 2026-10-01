

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiClient } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ApprovalDetailResponse, ApprovalDecision } from "@/types/api";
import { useParams, useRouter } from "next/navigation";
import { format } from "date-fns";
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  ClipboardList,
  ArrowLeft,
  AlertTriangle,
  ShieldCheck,
  ShieldX,
  RefreshCw,
  FileText as FileTextIcon,
  ClipboardCheck,
  Loader2,
} from "lucide-react";
import { LoadingButton } from "@/components/ui/loading/loading-spinner";
import { ErrorDisplay } from "@/components/ui/loading/error-display";
import { SkeletonTable } from "@/components/ui/loading/skeleton-card";
import { ActionPayload } from "./components/ActionPayload";

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { icon: React.ElementType; className: string }> = {
    pending: { icon: Clock, className: "bg-yellow-100 text-yellow-800" },
    approved: { icon: CheckCircle, className: "bg-green-100 text-green-800" },
    rejected: { icon: XCircle, className: "bg-red-100 text-red-800" },
    executed: { icon: ClipboardCheck, className: "bg-blue-100 text-blue-800" },
    failed: { icon: AlertTriangle, className: "bg-red-100 text-red-800" },
  };

  const config = statusConfig[status] || { icon: Clock, className: "bg-gray-100 text-gray-800" };
  const Icon = config.icon;

  return (
    <Badge className={`${config.className} gap-1`} variant="default">
      <Icon className="h-3 w-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

function RiskBadge({ level }: { level: string }) {
  const riskConfig: Record<string, { icon: React.ElementType; className: string }> = {
    LOW: { icon: Shield, className: "bg-green-100 text-green-800" },
    MEDIUM: { icon: AlertTriangle, className: "bg-yellow-100 text-yellow-800" },
    HIGH: { icon: AlertTriangle, className: "bg-red-100 text-red-800" },
  };

  const cfg = riskConfig[level] || riskConfig.MEDIUM;
  const Icon = cfg.icon;

  return (
    <Badge className={`${cfg.className} gap-1`} variant="default">
      <Icon className="h-3 w-3" />
      {level}
    </Badge>
  );
}

async function fetchApprovalDetail(approvalId: string) {
  return apiClient.getApprovalDetail(approvalId);
}

async function decideApproval(approvalId: string, decision: ApprovalDecision) {
  return apiClient.decideApproval(approvalId, decision);
}

export default function ApprovalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const approvalId = params.id as string;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["approval-detail", approvalId],
    queryFn: () => fetchApprovalDetail(approvalId),
    enabled: !!approvalId,
  });

  const decideMutation = useMutation({
    mutationFn: ({ approvalId, decision }: { approvalId: string; decision: ApprovalDecision }) =>
      decideApproval(approvalId, decision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approval-detail", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
    onError: (err: Error) => {
      alert(`Failed to process decision: ${err.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-accent rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-3xl font-bold tracking-tight">Approval Detail</h1>
        </div>
        <Card>
          <CardContent className="py-8">
            <div className="space-y-4">
              <SkeletonTable rows={1} />
              <SkeletonTable rows={1} />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-accent rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </button>
        </div>
        <Card className="border-red-200">
          <CardContent className="py-8 text-center text-red-600">
            Failed to load approval detail.
            <Button variant="outline" onClick={() => refetch()} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const approval = data?.approval;

  if (!approval) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-accent rounded-lg">
            <ArrowLeft className="h-5 w-5" />
          </button>
        </div>
        <Card className="border-red-200">
          <CardContent className="py-8 text-center text-red-600">
            Approval not found.
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleApprove = () => {
    decideMutation.mutate({
      approvalId,
      decision: {
        approval_id: approvalId,
        decision: "approved",
        decided_by: "human_operator",
        reason: "Approved via UI",
      },
    });
  };

  const handleReject = () => {
    const reason = prompt("Please provide a reason for rejection:");
    if (reason) {
      decideMutation.mutate({
        approvalId,
        decision: {
          approval_id: approvalId,
          decision: "rejected",
          decided_by: "human_operator",
          reason,
        },
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 hover:bg-accent rounded-lg">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-8 w-8" />
            Approval Detail
          </h1>
          <p className="text-muted-foreground">
            Review and decide on high-risk action approval
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => router.push("/approvals")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Queue
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Approval Request
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <StatusBadge status={approval.status} />
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Risk Level</p>
                <RiskBadge level={approval.risk_level} />
              </div>
            </div>

            <Separator />

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Approval ID</p>
                <p className="font-mono text-sm">{approval.id}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Resolution ID</p>
                <p className="font-mono text-sm">{approval.resolution_id}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Action Type</p>
                <p className="capitalize">{approval.action_type.replace("_", " ")}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Policy Rule</p>
                <p className="font-mono text-sm">{approval.policy_rule}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Requested At</p>
                <p className="text-sm">{format(new Date(approval.requested_at), "PPp")}</p>
              </div>
              {approval.decided_at && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Decided At</p>
                  <p className="text-sm">{format(new Date(approval.decided_at), "PPp")}</p>
                </div>
              )}
              {approval.decided_by && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Decided By</p>
                  <p className="text-sm">{approval.decided_by}</p>
                </div>
              )}
            </div>

            <Separator />

            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Reason</p>
              <p className="whitespace-pre-wrap">{approval.reason || "—"}</p>
            </div>

            {approval.decision_reason && (
              <div className="space-y-2 bg-muted/50 p-4 rounded-lg">
                <p className="text-sm text-muted-foreground">Decision Reason</p>
                <p className="whitespace-pre-wrap">{approval.decision_reason}</p>
              </div>
            )}

            {approval.status === "pending" && (
              <div className="pt-4 border-t flex gap-4">
                <LoadingButton
                  isLoading={decideMutation.isPending}
                  onClick={handleApprove}
                  variant="default"
                  className="flex-1 flex items-center justify-center gap-2"
                >
                  <ShieldCheck className="h-4 w-4" />
                  Approve
                </LoadingButton>
                <LoadingButton
                  isLoading={decideMutation.isPending}
                  onClick={handleReject}
                  variant="destructive"
                  className="flex-1 flex items-center justify-center gap-2"
                >
                  <ShieldX className="h-4 w-4" />
                  Reject
                </LoadingButton>
              </div>
            )}
          </CardContent>
        </Card>

        {data?.approval?.resolution ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileTextIcon className="h-5 w-5" />
                Associated Resolution
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">User Request</p>
                  <p className="whitespace-pre-wrap text-sm">{data.approval.resolution.user_request}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Intent</p>
                  <p className="capitalize">{data.approval.resolution.intent.replace("_", " ")}</p>
                </div>
                {data.approval.resolution.order_id && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Order ID</p>
                    <p className="font-mono text-sm">{data.approval.resolution.order_id}</p>
                  </div>
                )}
                {data.approval.resolution.order_number && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Order Number</p>
                    <p className="font-mono text-sm">{data.approval.resolution.order_number}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ) : null}

      <ActionPayload payload={approval.action_payload} />
    </div>
    </div>
  );
}