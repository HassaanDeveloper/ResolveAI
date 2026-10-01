from evaluation.models import (
    EvaluationScenario,
    ScenarioInput,
    ScenarioExpected,
    ExpectedToolCall,
    scenario_store,
)


# =============================================================================
# CANCELLATION SCENARIOS
# =============================================================================

# Scenario 6: Cancellation before shipment - auto-approve
scenario_store.add(EvaluationScenario(
    id="cancel_001",
    name="Cancellation before shipment - auto approve",
    description="Order 10001 in processing, cancellation should auto-approve",
    category="cancellation",
    input=ScenarioInput(
        request_id="eval_cancel_001",
        user_request="Cancel order 10001 please",
        order_id="10001",
    ),
    expected=ScenarioExpected(
        intent="cancellation_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10001"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10001"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "cancellation before shipment", "max_results": 5}),
            ExpectedToolCall(tool_name="cancel_order", arguments={"order_id": "10001", "operation_id": "cancel-order-10001"}),
        ],
        policy_result="ALLOW",
        action="cancel_order",
        final_state="COMPLETED",
        grounding=["Order Cancellation Policy v1.3 - Before Shipment"],
    ),
    tags=["auto_approve", "before_shipment"],
))


# Scenario 7: Cancellation after shipment - requires approval
scenario_store.add(EvaluationScenario(
    id="cancel_002",
    name="Cancellation after shipment - requires approval",
    description="Order 10612 shipped, cancellation requires approval",
    category="cancellation",
    input=ScenarioInput(
        request_id="eval_cancel_002",
        user_request="Cancel order 10612 please",
        order_id="10612",
    ),
    expected=ScenarioExpected(
        intent="cancellation_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10612"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10612"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "cancellation after shipment", "max_results": 5}),
        ],
        policy_result="REQUIRES_APPROVAL",
        action=None,
        final_state="PENDING_APPROVAL",
        grounding=["Order Cancellation Policy v1.3 - Post-Shipment Cancellations"],
    ),
    tags=["requires_approval", "after_shipment"],
))


# Scenario 8: Cancellation for delivered order - denied
scenario_store.add(EvaluationScenario(
    id="cancel_003",
    name="Cancellation for delivered order - denied",
    description="Order 10287 already delivered, cancellation denied",
    category="cancellation",
    input=ScenarioInput(
        request_id="eval_cancel_003",
        user_request="Cancel order 10287 please",
        order_id="10287",
    ),
    expected=ScenarioExpected(
        intent="cancellation_request",
        tools=[
            ExpectedToolCall(tool_name="get_order", arguments={"order_id": "10287"}),
            ExpectedToolCall(tool_name="get_shipping_status", arguments={"order_id": "10287"}),
            ExpectedToolCall(tool_name="search_company_policy", arguments={"query": "cancellation delivered order", "max_results": 5}),
        ],
        policy_result="DENY",
        action=None,
        final_state="REJECTED",
        grounding=["Order Cancellation Policy v1.3 - Post-Shipment Cancellations"],
    ),
    tags=["denied", "delivered"],
))