from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class AuditEventType(str, Enum):
    REQUEST_RECEIVED = "request_received"
    INTENT_IDENTIFIED = "intent_identified"
    ORDER_RETRIEVED = "order_retrieved"
    SHIPMENT_CHECKED = "shipment_checked"
    POLICY_RETRIEVED = "policy_retrieved"
    REFUND_CALCULATED = "refund_calculated"
    POLICY_EVALUATED = "policy_evaluated"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    ACTION_EXECUTED = "action_executed"
    ACTION_VERIFIED = "action_verified"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    ERROR_OCCURRED = "error_occurred"
    ESCALATION_CREATED = "escalation_created"


class AuditEvent(BaseModel):
    id: str
    request_id: str
    resolution_id: Optional[str] = None
    event_type: AuditEventType
    event_data: Dict[str, Any] = {}
    created_at: datetime


class AuditEventCreate(BaseModel):
    request_id: str
    resolution_id: Optional[str] = None
    event_type: AuditEventType
    event_data: Dict[str, Any] = {}


class VerificationResult(BaseModel):
    success: bool
    verified_at: datetime
    details: Dict[str, Any] = {}
    error: Optional[str] = None


class WorkflowTrace(BaseModel):
    """Complete trace of a workflow execution for audit purposes."""
    workflow_id: str
    request_id: str
    user_request: str
    intent: Optional[str] = None
    status: str
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    retrieved_documents: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    policy_result: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    action_result: Optional[Dict[str, Any]] = None
    verification: Optional[VerificationResult] = None
    final_status: Optional[str] = None
    errors: List[str] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    events: List[AuditEvent]
    total: int
    page: int
    page_size: int


class TraceResponse(BaseModel):
    trace: WorkflowTrace
    audit_events: List[AuditEvent]