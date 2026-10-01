from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime


class RealScenarioStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class RealScenarioInput(BaseModel):
    request_id: str
    user_request: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None


class RealExpectedPolicyDecision(BaseModel):
    decision: str  # ALLOW, DENY, REQUIRES_APPROVAL
    approval_tier: Optional[str] = None  # manager, director
    reason_contains: Optional[List[str]] = None


class RealExpectedApprovalState(BaseModel):
    expected_status: str  # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    transition_sequence: Optional[List[str]] = None  # e.g., ["PENDING", "APPROVED", "EXECUTED"]


class RealExpectedSideEffect(BaseModel):
    tool_name: str
    should_execute: bool
    expected_db_state: Optional[Dict[str, Any]] = None  # e.g., {"refunds.status": "completed"}
    expected_operation_status: Optional[str] = None  # executed, duplicate, failed


class RealExpectedEvidence(BaseModel):
    must_contain_sections: List[str] = []
    must_reference_document: Optional[str] = None
    min_relevance_score: float = 0.6
    must_have_evidence: bool = True


class RealExpectedGrounding(BaseModel):
    answer_references_evidence: bool = True
    no_unsupported_claims: bool = True


class RealScenarioExpectations(BaseModel):
    policy_decision: RealExpectedPolicyDecision
    approval_state: Optional[RealExpectedApprovalState] = None
    side_effects: List[RealExpectedSideEffect] = []
    evidence: Optional[RealExpectedEvidence] = None
    grounding: Optional[RealExpectedGrounding] = None
    final_workflow_status: str  # COMPLETED, REJECTED, PENDING_APPROVAL, FAILED


class RealIntegrationScenario(BaseModel):
    id: str
    name: str
    description: str
    category: str  # rag, policy, tool_execution, approval, side_effect_safety, llm
    requires_gemini: bool = False
    requires_supabase: bool = True
    requires_pgvector: bool = False
    input: RealScenarioInput
    expectations: RealScenarioExpectations
    tags: List[str] = []


class RealEvaluationResult(BaseModel):
    scenario_id: str
    scenario_name: str
    status: RealScenarioStatus
    duration_ms: int
    checks_passed: List[str] = []
    checks_failed: List[str] = []
    skip_reason: Optional[str] = None
    failure_reason: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None
    actual_policy_decision: Optional[str] = None
    actual_approval_state: Optional[str] = None
    actual_side_effects: List[Dict[str, Any]] = []
    actual_evidence: List[Dict[str, Any]] = []


class RealEvaluationSummary(BaseModel):
    total_scenarios: int
    passed: int
    failed: int
    skipped: int
    by_category: Dict[str, Dict[str, int]] = {}
    total_duration_ms: int
    timestamp: datetime
    results: List[RealEvaluationResult]


class RealScenarioStore:
    """Manages real integration evaluation scenarios."""
    
    def __init__(self):
        self.scenarios: List[RealIntegrationScenario] = []
    
    def add(self, scenario: RealIntegrationScenario) -> None:
        self.scenarios.append(scenario)
    
    def get_all(self) -> List[RealIntegrationScenario]:
        return self.scenarios
    
    def get_by_category(self, category: str) -> List[RealIntegrationScenario]:
        return [s for s in self.scenarios if s.category == category]
    
    def get_by_id(self, scenario_id: str) -> Optional[RealIntegrationScenario]:
        return next((s for s in self.scenarios if s.id == scenario_id), None)


# Global scenario store
real_scenario_store = RealScenarioStore()