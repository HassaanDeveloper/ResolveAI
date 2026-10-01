export type WorkflowStatus =
  | "pending"
  | "understanding"
  | "investigating"
  | "retrieving_policy"
  | "deciding"
  | "policy_check"
  | "pending_approval"
  | "executing"
  | "verifying"
  | "completed"
  | "rejected"
  | "failed";

export type WorkflowIntent =
  | "refund_request"
  | "cancellation_request"
  | "shipping_inquiry"
  | "escalation_request"
  | "unknown";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "executed" | "failed";

export type ApprovalActionType = "issue_refund" | "cancel_order" | "create_escalation";

export type AuditEventType =
  | "request_received"
  | "intent_identified"
  | "order_retrieved"
  | "shipment_checked"
  | "policy_retrieved"
  | "refund_calculated"
  | "policy_evaluated"
  | "approval_requested"
  | "approval_granted"
  | "approval_rejected"
  | "action_executed"
  | "action_verified"
  | "workflow_completed"
  | "workflow_failed"
  | "error_occurred"
  | "escalation_created";

export interface ToolCallRecord {
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  success: boolean;
  error?: string;
  timestamp: string;
}

export interface PolicyCheckRecord {
  action_type: string;
  decision: "ALLOW" | "DENY" | "REQUIRES_APPROVAL";
  reason: string;
  policy_rule: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  approval_tier?: string;
  conditions: string[];
}

export interface ApprovalRecord {
  approval_id?: string;
  status: string;
  requested_at?: string;
  decided_at?: string;
  decided_by?: string;
  reason?: string;
}

export interface VerificationRecord {
  success: boolean;
  verified_at: string;
  details: Record<string, unknown>;
  error?: string;
}

export interface ResolutionResponse {
    workflow_id: string;
    request_id: string;
    status: WorkflowStatus;
    intent: WorkflowIntent;
    user_request: string;
    order_id?: string;
    order_number?: string;
  policy_decision?: "ALLOW" | "DENY" | "REQUIRES_APPROVAL";
  policy_reason?: string;
  approval_required: boolean;
  approval_tier?: string;
  action_taken?: string;
  action_result?: Record<string, unknown>;
  verification_result?: Record<string, unknown>;
  final_message: string;
  errors: string[];
  // Trace fields (extended response)
  retrieved_documents?: Record<string, unknown>[];
  tool_calls?: ToolCallRecord[];
  policy_result?: PolicyCheckRecord;
  approval?: ApprovalRecord;
  verification?: VerificationRecord;
}

export interface CreateResolutionRequest {
  user_request: string;
  customer_id?: string;
  order_id?: string;
}

export interface ResolutionStatusResponse {
  workflow_id: string;
  request_id: string;
  status: WorkflowStatus;
  final_message: string;
}

export interface ApprovalRequest {
  id: string;
  resolution_id: string;
  action_type: ApprovalActionType;
  action_payload: Record<string, unknown>;
  reason: string;
  policy_rule: string;
  risk_level: string;
  status: ApprovalStatus;
  requested_at: string;
  decided_at?: string;
  decided_by?: string;
  decision_reason?: string;
}

export interface ApprovalCreate {
  resolution_id: string;
  action_type: ApprovalActionType;
  action_payload: Record<string, unknown>;
  reason: string;
  policy_rule: string;
  risk_level: string;
  requested_by?: string;
}

export interface ApprovalDecision {
  approval_id: string;
  decision: ApprovalStatus;
  decided_by: string;
  reason?: string;
}

export interface ApprovalResponse {
  approval: ApprovalRequest;
  message: string;
}

export interface ApprovalListItem {
  id: string;
  resolution_id: string;
  action_type: ApprovalActionType;
  reason: string;
  policy_rule: string;
  risk_level: string;
  status: ApprovalStatus;
  requested_at: string;
  decided_at?: string;
  decided_by?: string;
}

export interface ApprovalListResponse {
  approvals: ApprovalListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditEvent {
  id: string;
  request_id: string;
  resolution_id?: string;
  event_type: AuditEventType;
  event_data: Record<string, unknown>;
  created_at: string;
}

export interface AuditEventCreate {
  request_id: string;
  resolution_id?: string;
  event_type: AuditEventType;
  event_data: Record<string, unknown>;
}

export interface VerificationResult {
  success: boolean;
  verified_at: string;
  details: Record<string, unknown>;
  error?: string;
}

export interface WorkflowTrace {
  workflow_id: string;
  request_id: string;
  user_request: string;
  intent?: string;
  status: string;
  order_id?: string;
  order_number?: string;
  retrieved_documents: Record<string, unknown>[];
  tool_calls: ToolCallRecord[];
  policy_result?: Record<string, unknown>;
  approval?: Record<string, unknown>;
  action_result?: Record<string, unknown>;
  verification?: VerificationResult;
  final_status?: string;
  errors: string[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface AuditLogResponse {
  events: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
}

export interface TraceResponse {
  trace: WorkflowTrace;
  audit_events: AuditEvent[];
}

export interface HealthResponse {
  status: string;
  application: string;
  environment: string;
}

export interface DashboardMetrics {
  total_requests: number;
  successful_resolutions: number;
  pending_approvals: number;
  failed_resolutions: number;
  avg_resolution_time_ms: number | null;
}

export interface ApprovalDetailResponse extends ApprovalResponse {
  approval: ApprovalRequest & {
    resolution?: {
      user_request: string;
      intent: string;
      order_id?: string;
      order_number?: string;
    };
  };
}

export interface EvaluationResult {
  scenario_id: string;
  scenario_name: string;
  status: "PASS" | "FAIL" | "SKIPPED";
  duration_ms: number;
  checks_passed: string[];
  checks_failed: string[];
  skip_reason?: string;
  failure_reason?: string;
}

export interface EvaluationSummary {
  total_scenarios: number;
  passed: number;
  failed: number;
  skipped: number;
  by_category: Record<string, { passed: number; failed: number; skipped: number }>;
  total_duration_ms: number;
  timestamp: string;
  results: EvaluationResult[];
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  source: string;
  version: string;
  status: string;
  created_at: string;
  processed_at?: string;
  error?: string;
  chunk_count: number;
}

export interface DocumentsResponse {
  data: KnowledgeDocument[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  section: string;
  content: string;
  source: string;
  version: string;
  relevance_score: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  error: string | null;
  query: string;
  total_results: number;
}

export interface HealthResponse {
  status: string;
  application: string;
  environment: string;
}

export interface ApiError {
  detail: string;
}