import config from "./config";
import type {
  ResolutionResponse,
  CreateResolutionRequest,
  ResolutionStatusResponse,
  ApprovalListResponse,
  ApprovalRequest,
  ApprovalCreate,
  ApprovalDecision,
  ApprovalResponse,
  ApprovalDetailResponse,
  AuditLogResponse,
  AuditEventCreate,
  TraceResponse,
  WorkflowTrace,
  HealthResponse,
  DashboardMetrics,
  EvaluationSummary,
  DocumentsResponse,
  SearchResponse,
  KnowledgeDocument,
} from "@/types/api";

class ApiClient {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;

  constructor() {
    this.baseUrl = config.apiBaseUrl;
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  /**
   * Pull a human-readable message out of an error body.
   *
   * The backend uses two different shapes: validation/HTTPException responses
   * return `{ detail }`, while the generic handler returns
   * `{ error: { code, message } }`. Reading only `detail` left the console
   * showing an empty message for every internal error.
   */
  private extractErrorMessage(payload: unknown): string | null {
    if (typeof payload === "string" && payload.trim()) return payload;
    if (!payload || typeof payload !== "object") return null;

    const body = payload as Record<string, unknown>;
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    // FastAPI validation errors: detail is a list of error objects
    if (Array.isArray(detail) && detail.length > 0) {
      const messages = detail
        .map((item) =>
          item && typeof item === "object" && "msg" in (item as Record<string, unknown>)
            ? String((item as Record<string, unknown>).msg)
            : String(item)
        )
        .filter(Boolean);
      if (messages.length) return messages.join("; ");
    }

    const error = body.error;
    if (typeof error === "string" && error.trim()) return error;
    if (error && typeof error === "object" && "message" in (error as Record<string, unknown>)) {
      const message = (error as Record<string, unknown>).message;
      if (typeof message === "string" && message.trim()) return message;
    }

    if (typeof body.message === "string" && body.message.trim()) return body.message;
    return null;
  }

async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const requestId = typeof crypto !== "undefined" ? crypto.randomUUID() : "";

    // Merge with the Headers API: spreading a Headers instance copies nothing,
    // so deleted entries would be silently ignored.
    const headers = new Headers(this.defaultHeaders);
    new Headers(options.headers ?? {}).forEach((value, key) => {
      headers.set(key, value);
    });
    headers.set("X-Request-ID", requestId);

    // A FormData body must let the browser set multipart/form-data with its
    // boundary; an explicit application/json header breaks server-side parsing.
    if (typeof FormData !== "undefined" && options.body instanceof FormData) {
      headers.delete("Content-Type");
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const message =
          this.extractErrorMessage(payload) ?? `HTTP error ${response.status}`;
        throw new ApiErrorException(response.status, message);
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return undefined as T;
      }

      return response.json();
    } catch (err) {
      if (err instanceof TypeError && err.message === "Failed to fetch") {
        throw new ApiErrorException(0, "Network error: Unable to connect to the server. Please check if the backend is running and CORS is configured correctly.");
      }
      throw err;
    }
  }

  // Health
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health/");
  }

  // Resolutions
  async createResolution(
    request: CreateResolutionRequest
  ): Promise<ResolutionResponse> {
    return this.request<ResolutionResponse>("/resolutions/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getResolutionStatus(
    workflowId: string
  ): Promise<ResolutionStatusResponse> {
    return this.request<ResolutionStatusResponse>(
      `/resolutions/${workflowId}`
    );
  }

  async approveResolution(
    workflowId: string,
    approver: string = "human_operator"
  ): Promise<ResolutionResponse> {
    return this.request<ResolutionResponse>(
      `/resolutions/${workflowId}/approve`,
      {
        method: "POST",
        body: JSON.stringify({ approver }),
      }
    );
  }

  async rejectResolution(
    workflowId: string,
    reason: string,
    rejector: string = "human_operator"
  ): Promise<ResolutionResponse> {
    return this.request<ResolutionResponse>(
      `/resolutions/${workflowId}/reject`,
      {
        method: "POST",
        body: JSON.stringify({ reason, rejector }),
      }
    );
  }

  // Approvals
  async listApprovals(
    status?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApprovalListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) params.append("status", status);
    return this.request<ApprovalListResponse>(
      `/approvals/approvals?${params.toString()}`
    );
  }

  async getApproval(approvalId: string): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(`/approvals/approvals/${approvalId}`);
  }

  async createApproval(request: ApprovalCreate): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>("/approvals/approvals", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async decideApproval(
    approvalId: string,
    decision: ApprovalDecision
  ): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(
      `/approvals/approvals/${approvalId}/decide`,
      {
        method: "POST",
        body: JSON.stringify(decision),
      }
    );
  }

  async markApprovalExecuted(
    approvalId: string
  ): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(
      `/approvals/approvals/${approvalId}/execute`,
      {
        method: "POST",
      }
    );
  }

  async markApprovalFailed(
    approvalId: string,
    reason: string = "Execution failed"
  ): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(
      `/approvals/approvals/${approvalId}/fail`,
      {
        method: "POST",
        body: JSON.stringify({ reason }),
      }
    );
  }

  // Audit
  async listAuditEvents(
    requestId?: string,
    resolutionId?: string,
    eventType?: string,
    page: number = 1,
    pageSize: number = 50
  ): Promise<AuditLogResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (requestId) params.append("request_id", requestId);
    if (resolutionId) params.append("resolution_id", resolutionId);
    if (eventType) params.append("event_type", eventType);
    return this.request<AuditLogResponse>(`/audit/events?${params.toString()}`);
  }

  async recordAuditEvent(
    request: AuditEventCreate
  ): Promise<{ id: string; request_id: string; resolution_id?: string; event_type: string; event_data: Record<string, unknown>; created_at: string }> {
    return this.request("/audit/events", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async listWorkflowTraces(
    status?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<WorkflowTrace[]> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) params.append("status", status);
    return this.request<WorkflowTrace[]>(`/audit/traces?${params.toString()}`);
  }

  async getWorkflowTrace(workflowId: string): Promise<TraceResponse> {
    return this.request<TraceResponse>(`/audit/traces/${workflowId}`);
  }

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>("/dashboard/dashboard/metrics");
  }

  // Approvals - Detail
  async getApprovalDetail(approvalId: string): Promise<ApprovalDetailResponse> {
    return this.request<ApprovalDetailResponse>(`/approvals/approvals/${approvalId}/detail`);
  }

  // Evaluation
  async getEvaluationResults(): Promise<EvaluationSummary> {
    return this.request<EvaluationSummary>("/evaluation/results");
  }

  // Knowledge
  async getDocuments(): Promise<DocumentsResponse> {
    return this.request<DocumentsResponse>("/knowledge/documents");
  }

  async ingestDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_name", file.name);
    return this.request("/knowledge/documents/ingest", {
      method: "POST",
      body: formData,
    });
  }

  async ingestDocumentByName(filename: string): Promise<any> {
    return this.request("/knowledge/documents/ingest", {
      method: "POST",
      body: JSON.stringify({ filename }),
    });
  }

  async searchPolicies(query: string, maxResults?: number): Promise<SearchResponse> {
    return this.request<SearchResponse>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, max_results: maxResults || 5 }),
    });
  }
}

export class ApiErrorException extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = "ApiErrorException";
  }
}

export const apiClient = new ApiClient();