from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionType(str, Enum):
    ISSUE_REFUND = "issue_refund"
    CANCEL_ORDER = "cancel_order"
    CREATE_ESCALATION = "create_escalation"


class PolicyInput(BaseModel):
    action_type: ActionType
    order_status: Optional[str] = None
    shipment_status: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    currency: str = "USD"
    eligibility_satisfied: bool = False
    eligibility_reason: str = ""
    policy_evidence: List[Dict[str, Any]] = []
    customer_tier: Optional[str] = None
    is_high_value_customer: bool = False
    previous_escalations: int = 0


class PolicyOutput(BaseModel):
    decision: PolicyDecision
    reason: str
    policy_rule: str
    risk_level: RiskLevel
    requires_human_review: bool = False
    approval_tier: Optional[str] = None
    conditions: List[str] = []


class PolicyRule(BaseModel):
    name: str
    description: str
    condition: str
    decision: PolicyDecision
    priority: int = 0