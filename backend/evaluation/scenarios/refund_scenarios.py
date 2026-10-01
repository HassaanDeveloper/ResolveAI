from evaluation.models import (
    EvaluationScenario,
    ScenarioInput,
    ScenarioExpected,
    ExpectedToolCall,
    scenario_store,
)


# =============================================================================
# REFUND SCENARIOS
# =============================================================================

# Scenario 1: Delayed shipment refund - auto-approve (<= $100)
scenario_store.add(EvaluationScenario(
    id="refund_001",
    name="Delayed shipment refund - auto approve",
    description="Order 10482 delayed > 7 days, refund $74.99 should auto-approve",
    category="refund",
    input=ScenarioInput(
        request_id="eval_refund_001",
        user_request="Order 10482 hasn't arrived and I want a refund",
        customer_id="CUST-001",
        order_id="10482",
    ),
    expected=ScenarioExpected(
        intent="refund_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "refund delayed shipment", "max_results": 5}),
            ExpectedToolCall(tool_name="calculate_refund", arguments={"order_id": "10482"}),
            ExpectedToolCall(tool_name="issue_refund", arguments={"order_id": "10482", "amount": 74.99, "operation_id": "refund-order-10482-74.99"}),
        ],
        policy_result="ALLOW",
        action="issue_refund",
        final_state="COMPLETED",
        grounding=["Refund Policy v2.1 - Delayed Shipment Refunds", "Refund Policy v2.1 - Refund Approval Thresholds"],
    ),
    tags=["auto_approve", "delayed_shipment", "under_100"],
))


# Scenario 2: High-value delayed shipment refund - requires manager approval (> $100)
scenario_store.add(EvaluationScenario(
    id="refund_002",
    name="High-value delayed shipment refund - requires approval",
    description="Order 10521 delayed > 7 days, refund $299.99 requires manager approval",
    category="refund",
    input=ScenarioInput(
        request_id="eval_refund_002",
        user_request="Order 10521 hasn't arrived, need refund of $299.99",
        order_id="10521",
    ),
    expected=ScenarioExpected(
        intent="refund_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10521"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10521"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "refund delayed shipment", "max_results": 5}),
            ExpectedToolCall(tool_name="calculate_refund", arguments={"order_id": "10521"}),
        ],
        policy_result="REQUIRES_APPROVAL",
        action=None,  # No action until approved
        final_state="PENDING_APPROVAL",
        grounding=["Refund Policy v2.1 - Delayed Shipment Refunds", "Refund Approval Matrix - Tier 2"],
    ),
    tags=["requires_approval", "delayed_shipment", "over_100"],
))


# Scenario 3: Already refunded order
scenario_store.add(EvaluationScenario(
    id="refund_003",
    name="Already refunded order",
    description="Order 10356 already refunded, should be denied",
    category="refund",
    input=ScenarioInput(
        request_id="eval_refund_003",
        user_request="Order 10356 was already refunded but I want another refund",
        order_id="10356",
    ),
    expected=ScenarioExpected(
        intent="refund_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10356"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10356"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "refund already refunded", "max_results": 5}),
            ExpectedToolCall(tool_name="calculate_refund", arguments={"order_id": "10356"}),
        ],
        policy_result="DENY",
        action=None,
        final_state="REJECTED",
        grounding=["Refund Policy v2.1 - Refund Eligibility Criteria"],
    ),
    tags=["denied", "already_refunded"],
))


# Scenario 4: Delivered order outside 30-day window
scenario_store.add(EvaluationScenario(
    id="refund_004",
    name="Delivered order outside 30-day window",
    description="Order 10287 delivered > 30 days ago, refund should be denied",
    category="refund",
    input=ScenarioInput(
        request_id="eval_refund_004",
        user_request="Order 10287 delivered long ago, want refund",
        order_id="10287",
    ),
    expected=ScenarioExpected(
        intent="refund_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10287"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10287"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "refund delivered 30 days", "max_results": 5}),
            ExpectedToolCall(tool_name="calculate_refund", arguments={"order_id": "10287"}),
        ],
        policy_result="DENY",
        action=None,
        final_state="REJECTED",
        grounding=["Refund Policy v2.1 - Refund Eligibility Criteria"],
    ),
    tags=["denied", "outside_window", "delivered"],
))


# Scenario 5: Failed shipment refund
scenario_store.add(EvaluationScenario(
    id="refund_005",
    name="Failed shipment refund",
    description="Order 10602 shipment failed, refund should be allowed",
    category="refund",
    input=ScenarioInput(
        request_id="eval_refund_005",
        user_request="Order 10602 shipment failed, I want a refund",
        order_id="10602",
    ),
    expected=ScenarioExpected(
        intent="refund_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10602"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10602"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "refund failed shipment", "max_results": 5}),
            ExpectedToolCall(tool_name="calculate_refund", arguments={"order_id": "10602"}),
            ExpectedToolCall(tool_name="issue_refund", arguments={"order_id": "10602", "amount": 99.99, "operation_id": "refund-order-10602-99.99"}),
        ],
        policy_result="ALLOW",
        action="issue_refund",
        final_state="COMPLETED",
        grounding=["Refund Policy v2.1 - Carrier Loss or Damage"],
    ),
    tags=["auto_approve", "failed_shipment"],
))