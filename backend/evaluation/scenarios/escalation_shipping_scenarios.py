from evaluation.models import (
    EvaluationScenario,
    ScenarioInput,
    ScenarioExpected,
    ExpectedToolCall,
    scenario_store,
)


# =============================================================================
# ESCALATION SCENARIOS
# =============================================================================

# Scenario 9: High-value refund escalation
scenario_store.add(EvaluationScenario(
    id="escalation_001",
    name="High-value refund escalation",
    description="Order 10521 refund > $500 should escalate to director",
    category="escalation",
    input=ScenarioInput(
        request_id="eval_escalation_001",
        user_request="Order 10521 refund $750, need director approval",
        order_id="10521",
    ),
    expected=ScenarioExpected(
        intent="refund_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10521"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10521"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "refund approval director > 500", "max_results": 5}),
            ExpectedToolCall(tool_name="calculate_refund", arguments={"order_id": "10521"}),
        ],
        policy_result="REQUIRES_APPROVAL",
        action=None,
        final_state="PENDING_APPROVAL",
        grounding=["Refund Approval Matrix - Tier 3 (Director)"],
    ),
tags=["escalation", "director_approval", "high_value"],
))


# Scenario 10: Legal threat escalation
scenario_store.add(EvaluationScenario(
    id="escalation_002",
    name="Legal threat escalation",
    description="Customer threatens legal action, should escalate",
    category="escalation",
    input=ScenarioInput(
        request_id="eval_escalation_002",
        user_request="Order 10482 delayed, I'll sue if not refunded immediately!",
        order_id="10482",
    ),
    expected=ScenarioExpected(
        intent="escalation_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "legal threat escalation", "max_results": 5}),
            ExpectedToolCall(tool_name="create_escalation", arguments={"reason": "Legal threat", "context": {"order_id": "10482"}, "priority": "urgent"}),
        ],
        policy_result="ALLOW",
        action="create_escalation",
        final_state="COMPLETED",
        grounding=["Escalation SOP v1.0 - When to Escalate"],
    ),
    tags=["escalation", "legal_threat"],
))


# =============================================================================
# SHIPPING INQUIRY SCENARIOS
# =============================================================================

# Scenario 11: Shipping status inquiry
scenario_store.add(EvaluationScenario(
    id="shipping_001",
    name="Shipping status inquiry",
    description="Customer asks where order 10521 is",
    category="shipping_inquiry",
    input=ScenarioInput(
        request_id="eval_shipping_001",
        user_request="Where is my order 10521? It hasn't arrived yet.",
        order_id="10521",
    ),
    expected=ScenarioExpected(
        intent="shipping_inquiry",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10521"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10521"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "shipping delivery timeframe", "max_results": 5}),
        ],
        policy_result="ALLOW",
        action=None,
        final_state="COMPLETED",
        grounding=["Shipping Policy v1.5 - Delivery Timeframes"],
    ),
    tags=["inquiry", "status_check"],
))


# Scenario 12: Delayed shipment inquiry
scenario_store.add(EvaluationScenario(
    id="shipping_002",
    name="Delayed shipment inquiry",
    description="Customer asks about delayed order 10482",
    category="shipping_inquiry",
    input=ScenarioInput(
        request_id="eval_shipping_002",
        user_request="Where is my order 10482? It's been 2 weeks.",
        order_id="10482",
    ),
    expected=ScenarioExpected(
        intent="shipping_inquiry",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "delayed shipment refund eligibility", "max_results": 5}),
        ],
        policy_result="ALLOW",
        action=None,
        final_state="COMPLETED",
        grounding=["Shipping Policy v1.5 - Delivery Timeframes", "Refund Policy v2.1 - Delayed Shipment Refunds"],
    ),
    tags=["inquiry", "delayed_shipment"],
))