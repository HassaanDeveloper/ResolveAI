"""
Real Integration Evaluation Scenarios (Layer B)

These scenarios exercise the ACTUAL ResolveAI system:
- Real Supabase/pgvector
- Real Gemini embeddings
- Real tool execution
- Real policy engine
- Real approval service
- Real idempotency

Each scenario has INDEPENDENT expectations (not derived from implementation output).
"""

from evaluation.integration.models import (
    RealIntegrationScenario,
    RealScenarioInput,
    RealScenarioExpectations,
    RealExpectedPolicyDecision,
    RealExpectedApprovalState,
    RealExpectedSideEffect,
    RealExpectedEvidence,
    RealExpectedGrounding,
    real_scenario_store,
)
from evaluation.integration.fixtures import TEST_NAMESPACE
from decimal import Decimal


# =============================================================================
# RAG SCENARIOS
# =============================================================================

# Scenario RAG-001: Full RAG pipeline with seeded test document
real_scenario_store.add(RealIntegrationScenario(
    id="rag_001",
    name="Full RAG Pipeline - Document to Retrieval",
    description="Verify complete RAG pipeline: seeded test document -> chunking -> embedding -> pgvector storage -> vector query -> evidence retrieval",
    category="rag",
    requires_gemini=True,
    requires_supabase=True,
    requires_pgvector=True,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}rag-001",
        user_request="What is the refund policy for delayed shipments?",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="ALLOW",  # Not really used for RAG but required
        ),
        evidence=RealExpectedEvidence(
            must_have_evidence=True,
            must_contain_sections=["1.1 Eligibility"],
            must_reference_document="Test Refund Policy for Integration Evaluation",
            min_relevance_score=0.6,
        ),
        grounding=RealExpectedGrounding(
            answer_references_evidence=True,
            no_unsupported_claims=True,
        ),
        final_workflow_status="COMPLETED",
    ),
    tags=["rag", "full_pipeline", "grounding"],
))


# Scenario RAG-002: Carrier loss retrieval
real_scenario_store.add(RealIntegrationScenario(
    id="rag_002",
    name="RAG Retrieval - Carrier Loss Policy",
    description="Verify retrieval of carrier loss/damage policy section from seeded test document",
    category="rag",
    requires_gemini=True,
    requires_supabase=True,
    requires_pgvector=True,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}rag-002",
        user_request="What happens when a carrier loses my package?",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        evidence=RealExpectedEvidence(
            must_have_evidence=True,
            must_contain_sections=["2.1 Eligibility"],
            must_reference_document="Test Refund Policy for Integration Evaluation",
            min_relevance_score=0.6,
        ),
        grounding=RealExpectedGrounding(
            answer_references_evidence=True,
            no_unsupported_claims=True,
        ),
        final_workflow_status="COMPLETED",
    ),
    tags=["rag", "carrier_loss", "grounding"],
))


# =============================================================================
# POLICY SCENARIOS (Independent Expectations)
# =============================================================================

# Scenario POL-001: Delayed shipment refund <= $50 -> ALLOW (auto-approve)
real_scenario_store.add(RealIntegrationScenario(
    id="pol_001",
    name="Policy - Delayed Shipment Refund Auto-Approve (<= $50)",
    description="Test policy engine: delayed shipment refund $49.99 should be ALLOW (auto-approve per test policy threshold $50)",
    category="policy",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}pol-001",
        user_request=f"I want a refund for order {TEST_NAMESPACE}10001 - it's been delayed for 2 weeks",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10001",  # $49.99, delayed
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="ALLOW",
            approval_tier=None,
            reason_contains=["auto-approved", "auto-approve", "threshold"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=True,
                expected_db_state={"refunds.status": "completed"},
            ),
        ],
        final_workflow_status="COMPLETED",
    ),
    tags=["policy", "auto_approve", "delayed_shipment", "under_threshold"],
))


# Scenario POL-002: Delayed shipment refund > $50 -> REQUIRES_APPROVAL (manager)
real_scenario_store.add(RealIntegrationScenario(
    id="pol_002",
    name="Policy - Delayed Shipment Refund Requires Manager Approval (> $50)",
    description="Test policy engine: delayed shipment refund $150.00 should REQUIRE_APPROVAL from manager per policy engine",
    category="policy",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}pol-002",
        user_request=f"Order {TEST_NAMESPACE}10002 hasn't arrived, need refund of $150",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10002",  # $150.00, delayed
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="REQUIRES_APPROVAL",
            approval_tier="manager",
            reason_contains=["manager", "approval", "exceeds", "100"],
        ),
        approval_state=RealExpectedApprovalState(
            expected_status="PENDING",
            transition_sequence=["PENDING"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,  # Should NOT execute before approval
            ),
        ],
        final_workflow_status="PENDING_APPROVAL",
    ),
    tags=["policy", "requires_approval", "delayed_shipment", "over_threshold"],
))


# Scenario POL-003: Carrier loss refund -> REQUIRES_APPROVAL (manager)
real_scenario_store.add(RealIntegrationScenario(
    id="pol_003",
    name="Policy - Carrier Loss Refund Requires Manager Approval",
    description="Test policy engine: carrier loss refund $75.00 should REQUIRE_APPROVAL from manager per policy engine",
    category="policy",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}pol-003",
        user_request=f"Order {TEST_NAMESPACE}10003 shipment failed, carrier lost package, want refund",
        customer_id=f"{TEST_NAMESPACE}CUST-002",
        order_id=f"{TEST_NAMESPACE}10003",  # $75.00, failed shipment
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="REQUIRES_APPROVAL",
            approval_tier="manager",
            reason_contains=["approval", "carrier", "loss"],
        ),
        approval_state=RealExpectedApprovalState(
            expected_status="PENDING",
            transition_sequence=["PENDING"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,
            ),
        ],
        final_workflow_status="PENDING_APPROVAL",
    ),
    tags=["policy", "carrier_loss", "requires_approval"],
))


# Scenario POL-004: Delivered outside window -> DENY
real_scenario_store.add(RealIntegrationScenario(
    id="pol_004",
    name="Policy - Delivered Order Outside Window Denied",
    description="Test policy engine: delivered order 45 days ago should be DENIED",
    category="policy",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}pol-004",
        user_request=f"Order {TEST_NAMESPACE}10004 delivered long ago, want refund",
        customer_id=f"{TEST_NAMESPACE}CUST-002",
        order_id=f"{TEST_NAMESPACE}10004",  # $89.99, delivered 45 days ago
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="DENY",
            approval_tier=None,
            reason_contains=["denied", "outside", "window", "30-day"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,
            ),
        ],
        final_workflow_status="REJECTED",
    ),
    tags=["policy", "denied", "outside_window", "delivered"],
))


# Scenario POL-005: Cancellation before shipment -> ALLOW
real_scenario_store.add(RealIntegrationScenario(
    id="pol_005",
    name="Policy - Cancellation Before Shipment Auto-Approve",
    description="Test policy engine: cancellation for processing order should be ALLOW",
    category="policy",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}pol-005",
        user_request=f"Cancel order {TEST_NAMESPACE}10005 please",
        customer_id=f"{TEST_NAMESPACE}CUST-003",
        order_id=f"{TEST_NAMESPACE}10005",  # $120.00, processing (not shipped)
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="ALLOW",
            approval_tier=None,
            reason_contains=["auto-approved", "not yet shipped"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="cancel_order",
                should_execute=True,
                expected_db_state={"orders.status": "cancelled"},
            ),
        ],
        final_workflow_status="COMPLETED",
    ),
    tags=["policy", "cancellation", "auto_approve", "before_shipment"],
))


# Scenario POL-006: Cancellation after shipment -> REQUIRES_APPROVAL
real_scenario_store.add(RealIntegrationScenario(
    id="pol_006",
    name="Policy - Cancellation After Shipment Requires Approval",
    description="Test policy engine: cancellation for shipped order should REQUIRE_APPROVAL from manager per policy engine",
    category="policy",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}pol-006",
        user_request=f"Cancel order {TEST_NAMESPACE}10006 please",
        customer_id=f"{TEST_NAMESPACE}CUST-003",
        order_id=f"{TEST_NAMESPACE}10006",  # $200.00, shipped
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="REQUIRES_APPROVAL",
            approval_tier="manager",
            reason_contains=["approval", "already shipped", "shipped"],
        ),
        approval_state=RealExpectedApprovalState(
            expected_status="PENDING",
            transition_sequence=["PENDING"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="cancel_order",
                should_execute=False,
            ),
        ],
        final_workflow_status="PENDING_APPROVAL",
    ),
    tags=["policy", "cancellation", "requires_approval", "after_shipment"],
))


# =============================================================================
# TOOL EXECUTION SCENARIOS
# =============================================================================

# Scenario TOOL-001: Actual refund execution with real Supabase
real_scenario_store.add(RealIntegrationScenario(
    id="tool_001",
    name="Tool Execution - Real Refund Issuance",
    description="Execute actual issue_refund tool against real Supabase, verify refund record created",
    category="tool_execution",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}tool-001",
        user_request=f"Refund order {TEST_NAMESPACE}10010 - delayed shipment",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10010",  # $49.99, delayed, auto-approve
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="ALLOW",
            approval_tier=None,
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="get_order",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="get_shipping_status",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="search_company_policy",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="calculate_refund",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=True,
                expected_db_state={"refunds.status": "completed"},
            ),
        ],
        final_workflow_status="completed",
    ),
    tags=["tool_execution", "refund", "supabase", "side_effect"],
))


# Scenario TOOL-002: Actual cancellation execution
real_scenario_store.add(RealIntegrationScenario(
    id="tool_002",
    name="Tool Execution - Real Order Cancellation",
    description="Execute actual cancel_order tool against real Supabase, verify order status updated",
    category="tool_execution",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}tool-002",
        user_request=f"Cancel order {TEST_NAMESPACE}10011",
        customer_id=f"{TEST_NAMESPACE}CUST-003",
        order_id=f"{TEST_NAMESPACE}10011",  # Processing, not shipped
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="ALLOW",
            approval_tier=None,
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="get_order",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="get_shipping_status",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="search_company_policy",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="cancel_order",
                should_execute=True,
                expected_db_state={"orders.status": "cancelled"},
            ),
        ],
        final_workflow_status="completed",
    ),
    tags=["tool_execution", "cancellation", "supabase", "side_effect"],
))


# =============================================================================
# APPROVAL STATE TRANSITION SCENARIOS
# =============================================================================

# Scenario APP-001: Full approval lifecycle
real_scenario_store.add(RealIntegrationScenario(
    id="app_001",
    name="Approval Lifecycle - Create -> Pending -> Approve -> Execute",
    description="Verify complete approval lifecycle: workflow creates approval -> status PENDING -> simulate approval -> status APPROVED -> execution occurs -> status EXECUTED",
    category="approval",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}app-001",
        user_request=f"Order {TEST_NAMESPACE}10002 delayed, need refund of $150",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10002",  # $150, delayed, requires manager approval
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="REQUIRES_APPROVAL",
            approval_tier="test-manager",
        ),
        approval_state=RealExpectedApprovalState(
            expected_status="pending",
            transition_sequence=["pending"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,  # Not yet - needs approval first
            ),
        ],
        final_workflow_status="pending_approval",  # Initial state after workflow
    ),
    tags=["approval", "lifecycle", "pending_approval"],
))


# Scenario APP-002: Approval rejection
real_scenario_store.add(RealIntegrationScenario(
    id="app_002",
    name="Approval Lifecycle - Rejection",
    description="Verify approval rejection: workflow creates approval -> status PENDING -> simulate rejection -> status REJECTED -> workflow REJECTED",
    category="approval",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}app-002",
        user_request=f"Cancel order {TEST_NAMESPACE}10006 - shipped",
        customer_id=f"{TEST_NAMESPACE}CUST-003",
        order_id=f"{TEST_NAMESPACE}10006",  # $200, shipped, requires approval
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="REQUIRES_APPROVAL",
            approval_tier="test-manager",
        ),
        approval_state=RealExpectedApprovalState(
            expected_status="pending",
            transition_sequence=["pending"],
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="cancel_order",
                should_execute=False,
            ),
        ],
        final_workflow_status="pending_approval",
    ),
    tags=["approval", "rejection", "lifecycle"],
))


# =============================================================================
# SIDE-EFFECT SAFETY SCENARIOS
# =============================================================================

# Scenario SAFE-001: Allowed side effect executes
real_scenario_store.add(RealIntegrationScenario(
    id="safe_001",
    name="Side-Effect Safety - Allowed Action Executes",
    description="Verify that ALLOWED side-effect (refund) actually executes and creates database record",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-001",
        user_request=f"Refund order {TEST_NAMESPACE}10001 - delayed 2 weeks",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10001",  # $49.99, auto-approve
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=True,
                expected_db_state={"refunds.status": "completed"},
                expected_operation_status="executed",
            ),
        ],
        final_workflow_status="COMPLETED",
    ),
    tags=["safety", "allowed_executes", "refund"],
))


# Scenario SAFE-002: Denied action does NOT execute
real_scenario_store.add(RealIntegrationScenario(
    id="safe_002",
    name="Side-Effect Safety - Denied Action Blocked",
    description="Verify that DENIED action (refund for delivered outside window) does NOT execute",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-002",
        user_request=f"Refund order {TEST_NAMESPACE}10004 - delivered long ago",
        customer_id=f"{TEST_NAMESPACE}CUST-002",
        order_id=f"{TEST_NAMESPACE}10004",  # Delivered 45 days ago, denied
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="DENY"),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,
            ),
        ],
        final_workflow_status="REJECTED",
    ),
    tags=["safety", "denied_blocked", "refund"],
))


# Scenario SAFE-003: Approval-required action does NOT execute before approval
real_scenario_store.add(RealIntegrationScenario(
    id="safe_003",
    name="Side-Effect Safety - Approval Required Blocked Until Approved",
    description="Verify that REQUIRES_APPROVAL action does NOT execute before approval is granted",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-003",
        user_request=f"Refund order {TEST_NAMESPACE}10002 - delayed, $150",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10002",  # $150, requires manager approval
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(
            decision="REQUIRES_APPROVAL",
            approval_tier="test-manager",
        ),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,  # Should NOT execute yet
            ),
        ],
        final_workflow_status="PENDING_APPROVAL",
    ),
    tags=["safety", "approval_required_blocked", "refund"],
))


# Scenario SAFE-004: Idempotency - duplicate execution prevented
real_scenario_store.add(RealIntegrationScenario(
    id="safe_004",
    name="Side-Effect Safety - Idempotency Prevents Duplicate Refund",
    description="Verify that duplicate refund request with same operation_id is blocked (idempotent)",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-004",
        user_request=f"Refund order {TEST_NAMESPACE}10001 - duplicate request",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10001",  # $49.99, auto-approve
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=True,
                expected_operation_status="duplicate",  # Second execution should be duplicate
            ),
        ],
        final_workflow_status="COMPLETED",
    ),
    tags=["safety", "idempotency", "duplicate_prevention", "refund"],
))


# Scenario SAFE-005: Idempotency - duplicate cancellation prevented
real_scenario_store.add(RealIntegrationScenario(
    id="safe_005",
    name="Side-Effect Safety - Idempotency Prevents Duplicate Cancellation",
    description="Verify that duplicate cancellation request with same operation_id is blocked",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-005",
        user_request=f"Cancel order {TEST_NAMESPACE}10005 - duplicate request",
        customer_id=f"{TEST_NAMESPACE}CUST-003",
        order_id=f"{TEST_NAMESPACE}10005",  # Processing, auto-approve
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="cancel_order",
                should_execute=True,
                expected_operation_status="duplicate",
            ),
        ],
        final_workflow_status="COMPLETED",
    ),
    tags=["safety", "idempotency", "duplicate_prevention", "cancellation"],
))

# Scenario SAFE-006: Idempotency - duplicate refund prevention (fresh order)
real_scenario_store.add(RealIntegrationScenario(
    id="safe_006",
    name="Side-Effect Safety - Idempotency Prevents Duplicate Refund (Fresh Order)",
    description="Verify that duplicate refund request for eval-test-10008 with same operation_id is blocked (idempotent). Uses fresh order not used by other tests.",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-006",
        user_request=f"Refund order {TEST_NAMESPACE}10008 - delayed shipment",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10008",  # $49.99, delayed, auto-approve
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=True,
                expected_operation_status="executed",  # First execution
            ),
        ],
        final_workflow_status="COMPLETED",
    ),
    tags=["safety", "idempotency", "duplicate_prevention", "refund", "fresh_order"],
))

# Scenario SAFE-007: Idempotency - duplicate refund replay (second request)
real_scenario_store.add(RealIntegrationScenario(
    id="safe_007",
    name="Side-Effect Safety - Idempotency Duplicate Refund Replay",
    description="Verify that second refund request for eval-test-10008 is rejected because calculate_refund detects existing completed refund and returns eligible_amount=0. issue_refund is never called. Must be run after safe_006.",
    category="side_effect_safety",
    requires_gemini=False,
    requires_supabase=True,
    requires_pgvector=False,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}safe-007",
        user_request=f"Refund order {TEST_NAMESPACE}10008 - delayed shipment (replay)",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10008",  # Same order as safe_006
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="DENY"),
        side_effects=[
            RealExpectedSideEffect(
                tool_name="get_order",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="get_shipping_status",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="search_company_policy",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="calculate_refund",
                should_execute=True,
            ),
            RealExpectedSideEffect(
                tool_name="issue_refund",
                should_execute=False,  # Should NOT be called - duplicate prevented at calculate_refund level
            ),
        ],
        final_workflow_status="REJECTED",
    ),
    tags=["safety", "idempotency", "duplicate_prevention", "refund", "replay"],
))


# =============================================================================
# LLM EVALUATION SCENARIOS
# =============================================================================

# Scenario LLM-001: Real Gemini embedding + workflow
real_scenario_store.add(RealIntegrationScenario(
    id="llm_001",
    name="LLM Evaluation - Real Gemini Embedding in Workflow",
    description="Execute full workflow with real Gemini embedding generation for policy retrieval",
    category="llm",
    requires_gemini=True,
    requires_supabase=True,
    requires_pgvector=True,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}llm-001",
        user_request=f"Where is my order {TEST_NAMESPACE}10001? It's been delayed.",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
        order_id=f"{TEST_NAMESPACE}10001",
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        grounding=RealExpectedGrounding(
            answer_references_evidence=True,
            no_unsupported_claims=True,
        ),
        final_workflow_status="COMPLETED",
    ),
    tags=["llm", "gemini", "embedding", "grounding"],
))


# Scenario LLM-002: Real Gemini embedding for RAG query
real_scenario_store.add(RealIntegrationScenario(
    id="llm_002",
    name="LLM Evaluation - Real Gemini Query Embedding",
    description="Direct test of Gemini query embedding for RAG retrieval",
    category="llm",
    requires_gemini=True,
    requires_supabase=True,
    requires_pgvector=True,
    input=RealScenarioInput(
        request_id=f"{TEST_NAMESPACE}llm-002",
        user_request="What is the delayed shipment refund policy?",
        customer_id=f"{TEST_NAMESPACE}CUST-001",
    ),
    expectations=RealScenarioExpectations(
        policy_decision=RealExpectedPolicyDecision(decision="ALLOW"),
        evidence=RealExpectedEvidence(
            must_have_evidence=True,
            must_contain_sections=["Test Delayed Shipment Refunds"],
            min_relevance_score=0.6,
        ),
        grounding=RealExpectedGrounding(
            answer_references_evidence=True,
            no_unsupported_claims=True,
        ),
        final_workflow_status="COMPLETED",
    ),
    tags=["llm", "gemini", "embedding", "rag_query"],
))