"use client";

import { unstable_noStore } from "next/cache";
unstable_noStore();

import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { LoadingButton } from "@/components/ui/loading/loading-spinner";
import { ErrorDisplay } from "@/components/ui/loading/error-display";
import { apiClient } from "@/lib/api";
import { CreateResolutionRequest, ResolutionResponse, ToolCallRecord } from "@/types/api";
import { useMutation } from "@tanstack/react-query";
import { useRefresh } from "@/lib/refresh-context";
import { FileText, Search, Send, ArrowRight, Zap, BarChart3, RefreshCw, Plus } from "lucide-react";
import { ResolutionHeader } from "@/components/console/resolution-header";
import { WorkflowProgress } from "@/components/console/workflow-progress";
import { EvidenceSection } from "@/components/console/evidence-section";
import { EmptyState } from "@/components/ui/empty-state";

interface DocumentRecord {
  document_name?: string;
  name?: string;
  source?: string;
  section?: string;
  version?: string;
  relevance_score?: number;
  content?: string;
  data?: Record<string, unknown>;
}

interface AuditEvent {
  id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  created_at: string;
}

const SCENARIOS = [
  {
    label: "Low-Value Refund",
    icon: Zap,
    request: "My order hasn't arrived and I'd like a refund",
    customerId: "CUST-001",
    orderId: "10482",
    description: "$74.99 refund → expected ALLOW",
  },
  {
    label: "High-Value Refund",
    icon: BarChart3,
    request: "I want a refund for my recent order",
    customerId: "CUST-002",
    orderId: "10521",
    description: "$299.99 refund → expected REQUIRES_APPROVAL",
  },
  {
    label: "Out-of-Policy Refund",
    icon: RefreshCw,
    request: "I'd like a refund for order 10356",
    customerId: "CUST-003",
    orderId: "10356",
    description: "Already refunded → expected DENY",
  },
  {
    label: "Cancel Shipped Order",
    icon: ArrowRight,
    request: "Cancel my order 10482",
    customerId: "CUST-001",
    orderId: "10482",
    description: "Cancellation after shipment → expected REQUIRES_APPROVAL",
  },
];

export default function ResolutionConsolePage() {
  const [request, setRequest] = useState<CreateResolutionRequest>({
    user_request: "",
    customer_id: "",
    order_id: "",
  });

  const [result, setResult] = useState<ResolutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const requestFieldRef = useRef<HTMLTextAreaElement>(null);
  const { setRefreshFn } = useRefresh();

  // Register a real refresh with the layout navigation button. It re-reads the
  // status of the resolution currently on screen, in place, and is a no-op when
  // nothing has been submitted yet - it never clears the view or reloads.
  useEffect(() => {
    setRefreshFn(() => {
      if (!result?.workflow_id) return;
      setIsRefreshing(true);
      apiClient
        .getResolutionStatus(result.workflow_id)
        .then((status) => {
          setResult((prev) =>
            prev
              ? { ...prev, status: status.status, final_message: status.final_message }
              : prev
          );
          setError(null);
        })
        .catch((err: Error) => {
          setError(err.message || "Failed to refresh. Please try again.");
        })
        .finally(() => setIsRefreshing(false));
    });
    return () => setRefreshFn(null);
  }, [result?.workflow_id, setRefreshFn]);

  const mutation = useMutation({
    mutationFn: (req: CreateResolutionRequest) => apiClient.createResolution(req),
    onSuccess: (data) => {
      setResult(data);
      setError(null);
    },
 onError: (err: Error) => {
      const message = err instanceof Error && err.message.includes("Network error")
        ? err.message
        : err.message || "Failed to submit resolution. Please try again.";
      setError(message);
      setResult(null);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    mutation.mutate(request);
  };

  const handleReset = () => {
    setRequest({ user_request: "", customer_id: "", order_id: "" });
    setResult(null);
    setError(null);
  };

  // Start a brand new resolution without reloading the page: clears the form and
  // the previous result, then focuses the request field ready for typing.
  const handleNewRequest = useCallback(() => {
    setRequest({ user_request: "", customer_id: "", order_id: "" });
    setResult(null);
    setError(null);
    requestFieldRef.current?.focus();
  }, []);

  const applyScenario = (scenario: typeof SCENARIOS[0]) => {
    setRequest({
      user_request: scenario.request,
      customer_id: scenario.customerId,
      order_id: scenario.orderId,
    });
    setResult(null);
    setError(null);
  };

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-8 w-8" />
            Resolution Console
          </h1>
          <p className="text-muted-foreground mt-1">
            Submit a business resolution request and trace the full workflow execution.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              New Resolution Request
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="user_request">User Request</Label>
                <Textarea
                  id="user_request"
                  placeholder="e.g., Order 10482 hasn't arrived and I want a refund"
                  value={request.user_request}
                  onChange={(e) => setRequest({ ...request, user_request: e.target.value })}
                  required
                  rows={3}
                  className="min-h-[100px]"
                />
                <p className="text-sm text-muted-foreground">
                  Describe the customer&apos;s request in natural language.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="customer_id">Customer ID (optional)</Label>
                  <Input
                    id="customer_id"
                    placeholder="e.g., CUST-001"
                    value={request.customer_id}
                    onChange={(e) => setRequest({ ...request, customer_id: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="order_id">Order ID (optional)</Label>
                  <Input
                    id="order_id"
                    placeholder="e.g., 10482"
                    value={request.order_id}
                    onChange={(e) => setRequest({ ...request, order_id: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex gap-4">
                <LoadingButton
                  isLoading={mutation.isPending}
                  type="submit"
                  className="flex items-center gap-2"
                >
                  <Send className="h-4 w-4" />
                  Submit Resolution
                </LoadingButton>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleReset}
                  disabled={mutation.isPending}
                >
                  Reset
                </Button>
              </div>

              {error && <ErrorDisplay error={error} />}
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-h2">Try a Scenario</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-body-sm text-muted-foreground mb-4">
              Pre-fill the form with real Northstar Commerce orders to test different policy outcomes.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              {SCENARIOS.map((scenario) => {
                const Icon = scenario.icon;
                return (
                  <button
                    key={scenario.label}
                    type="button"
                    onClick={() => applyScenario(scenario)}
                    className="flex items-start gap-3 p-3 border border-border-default rounded-lg hover:bg-accent hover:shadow-sm transition-all duration-200 text-left surface-card"
                  >
                    <Icon className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <div>
                      <p className="font-medium text-body">{scenario.label}</p>
                      <p className="text-xs text-muted-foreground">{scenario.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <EmptyState
          title="No resolution submitted yet"
          description="Submit a resolution request above or try a scenario to see the full investigation, policy decision, execution, and verification trace."
          icon={<FileText />}
        />
      </div>
    );
  }

  const documents: DocumentRecord[] = result.retrieved_documents as DocumentRecord[] || [];
  const toolCalls: ToolCallRecord[] = result.tool_calls || [];
  const policyResult = result.policy_result;
  const approval = result.approval;
  const verification = result.verification;

  const auditEvents: AuditEvent[] = [];
  if (result.status) {
    auditEvents.push({
      id: "1",
      event_type: "request_received",
      event_data: { workflow_id: result.workflow_id, request_id: result.request_id },
      created_at: new Date().toISOString(),
    });
  }
  if (documents.length > 0) {
    auditEvents.push({
      id: "2",
      event_type: "policy_retrieved",
      event_data: { count: documents.length },
      created_at: new Date().toISOString(),
    });
  }
  if (policyResult) {
    auditEvents.push({
      id: "3",
      event_type: "policy_evaluated",
      event_data: { decision: policyResult.decision, rule: policyResult.policy_rule },
      created_at: new Date().toISOString(),
    });
  }
  if (approval) {
    auditEvents.push({
      id: "4",
      event_type: approval.status === "approved" ? "approval_granted" : "approval_rejected",
      event_data: { approval_id: approval.approval_id, decided_by: approval.decided_by },
      created_at: approval.decided_at || new Date().toISOString(),
    });
  }
  if (toolCalls.length > 0) {
    auditEvents.push({
      id: "5",
      event_type: "action_executed",
      event_data: { tools: toolCalls.map((t) => t.tool_name) },
      created_at: toolCalls[toolCalls.length - 1]?.timestamp || new Date().toISOString(),
    });
  }
  if (verification) {
    auditEvents.push({
      id: "6",
      event_type: verification.success ? "action_verified" : "workflow_failed",
      event_data: { verified: verification.success, details: verification.details },
      created_at: verification.verified_at,
    });
  }
  if (result.status === "completed") {
    auditEvents.push({
      id: "7",
      event_type: "workflow_completed",
      event_data: { final_message: result.final_message },
      created_at: new Date().toISOString(),
    });
  } else if (result.status === "failed" || result.status === "rejected") {
    auditEvents.push({
      id: "7",
      event_type: "workflow_failed",
      event_data: { errors: result.errors },
      created_at: new Date().toISOString(),
    });
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h1 className="text-display font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-8 w-8" />
            Resolution Console
          </h1>
          <div className="flex items-center gap-3">
            {isRefreshing && (
              <span className="text-body-sm text-muted-foreground flex items-center gap-1.5">
                <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                Refreshing…
              </span>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={handleNewRequest}
              disabled={mutation.isPending}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              New Request
            </Button>
          </div>
        </div>
        <p className="text-body text-muted-foreground mt-1">
          Submit a business resolution request and trace the full workflow execution.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            New Resolution Request
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="user_request">User Request</Label>
              <Textarea
                id="user_request"
                ref={requestFieldRef}
                placeholder="e.g., Order 10482 hasn't arrived and I want a refund"
                value={request.user_request}
                onChange={(e) => setRequest({ ...request, user_request: e.target.value })}
                required
                rows={3}
                className="min-h-[100px]"
              />
              <p className="text-sm text-muted-foreground">
                Describe the customer&apos;s request in natural language.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="customer_id">Customer ID (optional)</Label>
                <Input
                  id="customer_id"
                  placeholder="e.g., CUST-001"
                  value={request.customer_id}
                  onChange={(e) => setRequest({ ...request, customer_id: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="order_id">Order ID (optional)</Label>
                <Input
                  id="order_id"
                  placeholder="e.g., 10482"
                  value={request.order_id}
                  onChange={(e) => setRequest({ ...request, order_id: e.target.value })}
                />
              </div>
            </div>

            <div className="flex gap-4">
              <LoadingButton
                isLoading={mutation.isPending}
                type="submit"
                className="flex items-center gap-2"
              >
                <Send className="h-4 w-4" />
                Submit Resolution
              </LoadingButton>
              <Button
                type="button"
                variant="outline"
                onClick={handleReset}
                disabled={mutation.isPending}
              >
                Reset
              </Button>
            </div>

            {error && <ErrorDisplay error={error} />}
          </form>
        </CardContent>
      </Card>

      <ResolutionHeader result={result} />
      <WorkflowProgress
        currentStatus={result.status}
        toolCalls={toolCalls}
        retrievedDocuments={documents}
        errors={result.errors}
      />

      <div className="border border-border-default rounded-lg bg-surface-card p-4">
        <h3 className="text-h2 font-medium mb-3">Evidence</h3>
        <EvidenceSection documents={documents} status={result.status} />
      </div>
    </div>
  );
}
