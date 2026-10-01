from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime


class EvaluationMetric(str, Enum):
    TASK_SUCCESS = "task_success"
    TOOL_SELECTION_ACCURACY = "tool_selection_accuracy"
    ARGUMENT_ACCURACY = "argument_accuracy"
    POLICY_COMPLIANCE = "policy_compliance"
    GROUNDING = "grounding"
    CITATION_CORRECTNESS = "citation_correctness"
    HUMAN_ESCALATION_ACCURACY = "human_escalation_accuracy"
    SIDE_EFFECT_SAFETY = "side_effect_safety"
    LATENCY_MS = "latency_ms"
    FAILURE_RATE = "failure_rate"


class ScenarioInput(BaseModel):
    request_id: str
    user_request: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None


class ExpectedToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    optional: bool = False


class ScenarioExpected(BaseModel):
    intent: str
    tools: List[ExpectedToolCall] = []
    policy_result: Optional[str] = None  # ALLOW, DENY, REQUIRES_APPROVAL
    action: Optional[str] = None  # issue_refund, cancel_order, create_escalation
    final_state: str  # COMPLETED, REJECTED, PENDING_APPROVAL, FAILED
    grounding: Optional[List[str]] = None  # Expected policy sections/documents


class EvaluationScenario(BaseModel):
    id: str
    name: str
    description: str
    category: str  # refund, cancellation, escalation, shipping_inquiry
    input: ScenarioInput
    expected: ScenarioExpected
    tags: List[str] = []


class EvaluationResult(BaseModel):
    scenario_id: str
    scenario_name: str
    passed: bool
    metrics: Dict[str, Any]
    latency_ms: int
    errors: List[str] = []
    trace: Optional[Dict[str, Any]] = None


class EvaluationSummary(BaseModel):
    total_scenarios: int
    passed: int
    failed: int
    metrics: Dict[str, float]
    total_latency_ms: int
    timestamp: datetime
    results: List[EvaluationResult]


class ScenarioStore:
    """Manages evaluation scenarios."""
    
    def __init__(self):
        self.scenarios: List[EvaluationScenario] = []
    
    def add(self, scenario: EvaluationScenario) -> None:
        self.scenarios.append(scenario)
    
    def get_all(self) -> List[EvaluationScenario]:
        return self.scenarios
    
    def get_by_category(self, category: str) -> List[EvaluationScenario]:
        return [s for s in self.scenarios if s.category == category]
    
    def get_by_id(self, scenario_id: str) -> Optional[EvaluationScenario]:
        return next((s for s in self.scenarios if s.id == scenario_id), None)


# Global scenario store
scenario_store = ScenarioStore()