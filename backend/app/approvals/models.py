from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class ApprovalActionType(str, Enum):
    ISSUE_REFUND = "issue_refund"
    CANCEL_ORDER = "cancel_order"
    CREATE_ESCALATION = "create_escalation"


class ApprovalRequest(BaseModel):
    id: str
    resolution_id: str
    action_type: ApprovalActionType
    action_payload: Dict[str, Any]
    reason: str
    policy_rule: str
    risk_level: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_reason: Optional[str] = None


class ApprovalCreate(BaseModel):
    resolution_id: str
    action_type: ApprovalActionType
    action_payload: Dict[str, Any]
    reason: str
    policy_rule: str
    risk_level: str
    requested_by: Optional[str] = "system"


class ApprovalDecision(BaseModel):
    approval_id: str
    decision: ApprovalStatus  # APPROVED or REJECTED
    decided_by: str = "human_operator"
    reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    approval: ApprovalRequest
    message: str


class ApprovalListItem(BaseModel):
    id: str
    resolution_id: str
    action_type: ApprovalActionType
    reason: str
    policy_rule: str
    risk_level: str
    status: ApprovalStatus
    requested_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None


class ApprovalListResponse(BaseModel):
    approvals: List[ApprovalListItem]
    total: int
    page: int
    page_size: int


# Database row to model conversion helpers
def approval_from_db(row: Dict[str, Any]) -> ApprovalRequest:
    """Convert database row to ApprovalRequest model."""
    return ApprovalRequest(
        id=row["id"],
        resolution_id=row["resolution_id"],
        action_type=ApprovalActionType(row["action_type"]),
        action_payload=row["action_payload"],
        reason=row["reason"],
        policy_rule=row.get("policy_rule", ""),
        risk_level=row.get("risk_level", "MEDIUM"),
        status=ApprovalStatus(row["status"]),
        requested_at=row["requested_at"],
        decided_at=row.get("decided_at"),
        decided_by=row.get("decided_by"),
        decision_reason=row.get("decision_reason"),
    )


def approval_list_item_from_db(row: Dict[str, Any]) -> ApprovalListItem:
    """Convert database row to ApprovalListItem model."""
    return ApprovalListItem(
        id=row["id"],
        resolution_id=row["resolution_id"],
        action_type=ApprovalActionType(row["action_type"]),
        reason=row["reason"],
        policy_rule=row.get("policy_rule", ""),
        risk_level=row.get("risk_level", "MEDIUM"),
        status=ApprovalStatus(row["status"]),
        requested_at=row["requested_at"],
        decided_at=row.get("decided_at"),
        decided_by=row.get("decided_by"),
    )