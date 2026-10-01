from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    UNDERSTANDING = "understanding"
    INVESTIGATING = "investigating"
    RETRIEVING_POLICY = "retrieving_policy"
    DECIDING = "deciding"
    POLICY_CHECK = "policy_check"
    PENDING_APPROVAL = "pending_approval"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class WorkflowIntent(str, Enum):
    REFUND_REQUEST = "refund_request"
    CANCELLATION_REQUEST = "cancellation_request"
    SHIPPING_INQUIRY = "shipping_inquiry"
    ESCALATION_REQUEST = "escalation_request"
    UNKNOWN = "unknown"


class ToolCallRecord(BaseModel):
    tool_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    success: bool
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PolicyCheckRecord(BaseModel):
    action_type: str
    decision: str
    reason: str
    policy_rule: str
    risk_level: str
    approval_tier: Optional[str] = None
    conditions: List[str] = []


class ApprovalRecord(BaseModel):
    approval_id: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    requested_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    reason: Optional[str] = None


class VerificationRecord(BaseModel):
    success: bool
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = {}
    error: Optional[str] = None


class ResolutionWorkflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    user_request: str
    intent: WorkflowIntent = WorkflowIntent.UNKNOWN
    status: WorkflowStatus = WorkflowStatus.PENDING
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    retrieved_documents: List[Dict[str, Any]] = []
    tool_calls: List[ToolCallRecord] = []
    policy_result: Optional[PolicyCheckRecord] = None
    approval: Optional[ApprovalRecord] = None
    action_result: Optional[Dict[str, Any]] = None
    verification: Optional[VerificationRecord] = None
    final_status: Optional[str] = None
    errors: List[str] = []
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ResolutionRequest(BaseModel):
    request_id: str
    user_request: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None


class ResolutionResponse(BaseModel):
    workflow_id: str
    request_id: str
    status: WorkflowStatus
    intent: WorkflowIntent
    user_request: str
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    policy_decision: Optional[str] = None
    policy_reason: Optional[str] = None
    approval_required: bool = False
    approval_tier: Optional[str] = None
    action_taken: Optional[str] = None
    action_result: Optional[Dict[str, Any]] = None
    verification_result: Optional[Dict[str, Any]] = None
    final_message: str
    errors: List[str] = []
    idempotent_replay: bool = False


class WorkflowStepResult(BaseModel):
    success: bool
    workflow: ResolutionWorkflow
    message: str
    next_step: Optional[str] = None