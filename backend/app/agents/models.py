from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from app.tools.schemas.base import ToolResult


class AgentStepType(str, Enum):
    ANALYZE = "analyze"
    SELECT_TOOL = "select_tool"
    EXECUTE_TOOL = "execute_tool"
    SYNTHESIZE = "synthesize"
    FINAL_ANSWER = "final_answer"


class AgentAction(BaseModel):
    """Structured action the agent wants to take."""
    step_type: AgentStepType
    reasoning: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    state_update: Dict[str, Any] = Field(default_factory=dict)


class AgentObservation(BaseModel):
    """Result of executing a tool."""
    tool_name: str
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """Current state of the agent loop."""
    request_id: str
    user_request: str
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    intent: Optional[str] = None
    steps_taken: int = 0
    tool_errors: int = 0
    max_steps: int = 10
    tool_error_limit: int = 3
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_step_at: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    observations: List[AgentObservation] = []
    evidence: List[Dict[str, Any]] = []
    is_complete: bool = False
    final_answer: Optional[str] = None


class AgentResponse(BaseModel):
    """Structured response from the agent."""
    action: AgentAction
    state_update: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for the agent."""
    max_steps: int = 10
    tool_error_limit: int = 3
    timeout_seconds: int = 60
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.1


# Allowed tools for the agent (read-only tools)
ALLOWED_READ_TOOLS = [
    "get_order",
    "get_customer", 
    "get_shipping_status",
    "search_company_policy",
    "calculate_refund",
]

# Side-effect tools (require policy approval, agent cannot directly execute)
SIDE_EFFECT_TOOLS = [
    "issue_refund",
    "cancel_order",
    "create_escalation",
]


def get_tool_descriptions() -> List[Dict[str, Any]]:
    """Get descriptions of allowed tools for the agent prompt."""
    return [
        {
            "name": "get_order",
            "description": "Retrieve order details by order number",
            "parameters": {"order_id": "string"},
            "returns": "Order details including status, amount, customer"
        },
        {
            "name": "get_customer",
            "description": "Retrieve customer details by external customer ID",
            "parameters": {"customer_id": "string"},
            "returns": "Customer details including name, email, account status"
        },
        {
            "name": "get_shipping_status",
            "description": "Retrieve shipment tracking information for an order",
            "parameters": {"order_id": "string"},
            "returns": "Shipment details including carrier, tracking number, status, estimated delivery"
        },
        {
            "name": "search_company_policy",
            "description": "Search company policies for relevant information",
            "parameters": {"query": "string", "max_results": "integer (optional, default 5)"},
            "returns": "Policy excerpts with document name, section, relevance score"
        },
        {
            "name": "calculate_refund",
            "description": "Calculate eligible refund amount for an order based on policy",
            "parameters": {"order_id": "string"},
            "returns": "Refund calculation with eligible amount, reason, policy references"
        },
    ]