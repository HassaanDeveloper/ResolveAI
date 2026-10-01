from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: str
    customer_name: str
    status: str
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class CustomerResponse(BaseModel):
    id: str
    external_customer_id: str
    name: str
    email: str
    account_status: str
    created_at: datetime


class ShipmentResponse(BaseModel):
    id: str
    order_id: str
    carrier: str
    tracking_number: str
    status: str
    estimated_delivery_date: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    updated_at: datetime


class PolicySearchResult(BaseModel):
    document_name: str
    section: str
    content: str
    source: Optional[str] = None
    version: Optional[str] = None
    relevance_score: Optional[float] = None


class RefundCalculation(BaseModel):
    order_id: str
    order_number: str
    eligible_amount: Decimal
    currency: str
    eligibility_reason: str
    policy_references: list[PolicySearchResult] = []


class RefundIssueResult(BaseModel):
    success: bool
    refund_id: Optional[str] = None
    operation_id: str
    amount: Decimal
    currency: str
    status: str
    message: str
    processed_at: Optional[datetime] = None
    idempotent_replay: bool = False


class CancellationResult(BaseModel):
    success: bool
    order_id: str
    order_number: str
    operation_id: str
    status: str
    message: str
    requires_approval: bool = False


class EscalationResult(BaseModel):
    success: bool
    escalation_id: str
    reason: str
    status: str
    message: str
    created_at: datetime


class ToolError(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: dict = {}


class ToolResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[ToolError] = None


class ToolCategory(str, Enum):
    READ = "read"
    SIDE_EFFECT = "side_effect"


class ToolInput(BaseModel):
    pass


class ToolOutput(BaseModel):
    pass


class BaseTool(BaseModel):
    name: str
    category: ToolCategory
    description: str
    requires_approval: bool = False