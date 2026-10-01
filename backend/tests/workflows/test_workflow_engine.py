import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from app.workflows.engine import WorkflowEngine
from app.workflows.models import ResolutionRequest, ResolutionResponse, WorkflowIntent, WorkflowStatus


@pytest.fixture
def workflow_engine():
    return WorkflowEngine()


@pytest.fixture
def sample_resolution_request():
    return ResolutionRequest(
        request_id="req-test-123",
        user_request="Order 10482 hasn't arrived and I want a refund",
        customer_id="CUST-001",
        order_id="10482",
    )


@pytest.mark.asyncio
async def test_extract_order_id(workflow_engine):
    """Test order ID extraction from user request."""
    assert workflow_engine._extract_order_id("Order 10482 hasn't arrived") == "10482"
    assert workflow_engine._extract_order_id("My order #10521 is delayed") == "10521"
    assert workflow_engine._extract_order_id("Refund for order 10356 please") == "10356"
    assert workflow_engine._extract_order_id("No order number here") is None
    assert workflow_engine._extract_order_id("Order 1234 is wrong format") is None


@pytest.mark.asyncio
async def test_classify_intent(workflow_engine):
    """Test intent classification."""
    assert workflow_engine._classify_intent("I want a refund for order 10482") == WorkflowIntent.REFUND_REQUEST
    assert workflow_engine._classify_intent("Please cancel my order 10521") == WorkflowIntent.CANCELLATION_REQUEST
    assert workflow_engine._classify_intent("Where is my shipment 10482?") == WorkflowIntent.SHIPPING_INQUIRY
    assert workflow_engine._classify_intent("I want to speak to a manager") == WorkflowIntent.ESCALATION_REQUEST
    assert workflow_engine._classify_intent("Hello world") == WorkflowIntent.UNKNOWN


# =============================================
# INTEGRATION TESTS WITH MOCKED TOOLS
# =============================================

@pytest.fixture
def mock_tools():
    """Mock all tool registry calls, approval service, and audit service."""
    with patch("app.workflows.engine.tool_registry") as mock_registry, \
         patch("app.workflows.engine.approval_service") as mock_approval, \
         patch("app.workflows.engine.audit_service") as mock_audit:
        # Create a list of responses
        responses = []
        mock_registry.execute = AsyncMock(side_effect=lambda *args, **kwargs: responses.pop(0) if responses else AsyncMock(success=False, error=MagicMock(message="No mock response")))
        
        # Default approval service mocks
        mock_approval.create_approval = AsyncMock(return_value=MagicMock(
            approval=MagicMock(id="test-approval-id"),
            message="Approval created"
        ))
        mock_approval.get_approval = AsyncMock(return_value=MagicMock(
            id="test-approval-id",
            status="pending"
        ))
        mock_approval.transition_to_executed = AsyncMock()
        mock_approval.transition_to_failed = AsyncMock()
        
        # Default audit service mocks
        mock_audit.record_event_simple = AsyncMock(return_value=MagicMock(
            id="test-audit-id",
            request_id="test-request-id",
            event_type="test_event",
            event_data={},
            created_at="2025-01-01T00:00:00+00:00"
        ))
        
        yield mock_registry, responses, mock_approval, mock_audit


@pytest.mark.asyncio
async def test_workflow_refund_delayed_shipment_auto_approve(mock_tools, sample_resolution_request):
    """Test full workflow for delayed shipment refund (auto-approve <= $100)."""
    mock_registry, responses, mock_approval, mock_audit = mock_tools
    
    # Build response objects
    from app.tools.schemas.base import ToolResult
    
    responses.extend([
        # get_order
        ToolResult(success=True, data={
            "order": {
                "id": "order-uuid-1",
                "order_number": "10482",
                "customer_id": "cust-uuid-1",
                "customer_name": "Sarah Mitchell",
                "status": "shipped",
                "total_amount": 74.99,
                "currency": "USD",
                "created_at": "2025-08-01T10:00:00+00:00",
                "updated_at": "2025-08-01T10:00:00+00:00",
            }
        }),
        # get_shipping_status
        ToolResult(success=True, data={
            "shipment": {
                "id": "shipment-uuid-1",
                "order_id": "order-uuid-1",
                "carrier": "FedEx",
                "tracking_number": "FX123456789US",
                "status": "delayed",
                "estimated_delivery_date": "2025-08-01",
                "delivered_at": None,
                "updated_at": "2025-08-20T10:00:00+00:00",
            }
        }),
        # search_company_policy
        ToolResult(success=True, data={
            "results": [
                {"document_name": "Refund Policy", "section": "Delayed Shipments", "content": "..."}
            ]
        }),
        # calculate_refund
        ToolResult(success=True, data={
            "calculation": {
                "order_id": "order-uuid-1",
                "order_number": "10482",
                "eligible_amount": 74.99,
                "currency": "USD",
                "eligibility_reason": "Delayed > 7 days",
                "policy_references": []
            }
        }),
        # issue_refund (execution)
        ToolResult(success=True, data={
            "result": {
                "success": True,
                "refund_id": "refund-uuid-1",
                "operation_id": "refund-order-10482-74.99",
                "amount": 74.99,
                "currency": "USD",
                "status": "completed",
                "message": "Refund processed",
                "processed_at": "2025-08-25T10:00:00+00:00"
            }
        }),
    ])

    engine = WorkflowEngine()
    workflow = await engine.execute(sample_resolution_request)

    assert workflow.intent == WorkflowIntent.REFUND_REQUEST
    assert workflow.order_number == "10482"
    assert workflow.status == WorkflowStatus.COMPLETED
    assert workflow.final_status == "completed"
    assert workflow.policy_result is not None
    assert workflow.policy_result.decision == "ALLOW"
    assert workflow.action_result is not None
    assert workflow.verification is not None
    assert workflow.verification.success is True


@pytest.mark.asyncio
async def test_workflow_refund_high_value_requires_approval(mock_tools):
    """Test workflow for high-value refund requiring approval."""
    mock_registry, responses, mock_approval, mock_audit = mock_tools
    
    from app.tools.schemas.base import ToolResult
    
    request = ResolutionRequest(
        request_id="req-test-456",
        user_request="Order 10521 hasn't arrived, need refund of $299.99",
        order_id="10521",
    )

    responses.extend([
        # get_order
        ToolResult(success=True, data={
            "order": {
                "id": "order-uuid-2",
                "order_number": "10521",
                "customer_id": "cust-uuid-2",
                "customer_name": "James Chen",
                "status": "shipped",
                "total_amount": 299.99,
                "currency": "USD",
                "created_at": "2025-08-01T10:00:00+00:00",
                "updated_at": "2025-08-01T10:00:00+00:00",
            }
        }),
        # get_shipping_status
        ToolResult(success=True, data={
            "shipment": {
                "id": "shipment-uuid-2",
                "order_id": "order-uuid-2",
                "carrier": "UPS",
                "tracking_number": "1Z999AA10123456784",
                "status": "in_transit",
                "estimated_delivery_date": "2025-09-10",
                "delivered_at": None,
                "updated_at": "2025-09-01T10:00:00+00:00",
            }
        }),
        # search_company_policy
        ToolResult(success=True, data={"results": []}),
        # calculate_refund
        ToolResult(success=True, data={
            "calculation": {
                "order_id": "order-uuid-2",
                "order_number": "10521",
                "eligible_amount": 299.99,
                "currency": "USD",
                "eligibility_reason": "Delayed > 7 days",
                "policy_references": []
            }
        }),
    ])

    engine = WorkflowEngine()
    workflow = await engine.execute(request)

    assert workflow.intent == WorkflowIntent.REFUND_REQUEST
    assert workflow.order_number == "10521"
    assert workflow.status == WorkflowStatus.PENDING_APPROVAL
    assert workflow.policy_result is not None
    assert workflow.policy_result.decision == "REQUIRES_APPROVAL"
    assert workflow.policy_result.approval_tier == "manager"
    assert workflow.approval is not None
    assert workflow.approval.status == "pending"


@pytest.mark.asyncio
async def test_workflow_refund_denied_eligibility(mock_tools):
    """Test workflow for refund denied due to eligibility."""
    mock_registry, responses, mock_approval, mock_audit = mock_tools
    
    from app.tools.schemas.base import ToolResult
    
    request = ResolutionRequest(
        request_id="req-test-789",
        user_request="Order 10287 delivered long ago, want refund",
        order_id="10287",
    )

    responses.extend([
        # get_order
        ToolResult(success=True, data={
            "order": {
                "id": "order-uuid-3",
                "order_number": "10287",
                "customer_id": "cust-uuid-3",
                "customer_name": "David Thompson",
                "status": "delivered",
                "total_amount": 89.99,
                "currency": "USD",
                "created_at": "2025-06-01T10:00:00+00:00",
                "updated_at": "2025-06-01T10:00:00+00:00",
            }
        }),
        # get_shipping_status
        ToolResult(success=True, data={
            "shipment": {
                "id": "shipment-uuid-3",
                "order_id": "order-uuid-3",
                "carrier": "FedEx",
                "tracking_number": "FX987654321US",
                "status": "delivered",
                "estimated_delivery_date": "2025-06-15",
                "delivered_at": "2025-06-14T10:15:00+00:00",
                "updated_at": "2025-06-14T10:15:00+00:00",
            }
        }),
        # search_company_policy
        ToolResult(success=True, data={"results": []}),
        # calculate_refund
        ToolResult(success=True, data={
            "calculation": {
                "order_id": "order-uuid-3",
                "order_number": "10287",
                "eligible_amount": 0,
                "currency": "USD",
                "eligibility_reason": "Delivered 45 days ago, outside 30-day policy",
                "policy_references": []
            }
        }),
    ])

    engine = WorkflowEngine()
    workflow = await engine.execute(request)

    assert workflow.intent == WorkflowIntent.REFUND_REQUEST
    assert workflow.status == WorkflowStatus.REJECTED
    assert workflow.final_status == "rejected"
    assert workflow.policy_result is not None
    assert workflow.policy_result.decision == "DENY"
    assert "outside 30-day" in workflow.policy_result.reason


@pytest.mark.asyncio
async def test_workflow_cancellation_shipped_requires_approval(mock_tools):
    """Test cancellation workflow for shipped order."""
    mock_registry, responses, mock_approval, mock_audit = mock_tools
    
    from app.tools.schemas.base import ToolResult
    
    request = ResolutionRequest(
        request_id="req-test-cancel",
        user_request="Cancel order 10612 please",
        order_id="10612",
    )

    responses.extend([
        # get_order
        ToolResult(success=True, data={
            "order": {
                "id": "order-uuid-4",
                "order_number": "10612",
                "customer_id": "cust-uuid-4",
                "customer_name": "Jennifer Park",
                "status": "shipped",
                "total_amount": 199.99,
                "currency": "USD",
                "created_at": "2025-08-01T10:00:00+00:00",
                "updated_at": "2025-08-01T10:00:00+00:00",
            }
        }),
        # get_shipping_status
        ToolResult(success=True, data={
            "shipment": {
                "id": "shipment-uuid-4",
                "order_id": "order-uuid-4",
                "carrier": "UPS",
                "tracking_number": "1Z999AA10123456785",
                "status": "in_transit",
                "estimated_delivery_date": "2025-09-12",
                "delivered_at": None,
                "updated_at": "2025-09-01T10:00:00+00:00",
            }
        }),
        # search_company_policy
        ToolResult(success=True, data={"results": []}),
        # calculate_refund (not called for cancellation, but let's include)
        ToolResult(success=True, data={"calculation": {"eligible_amount": 0}}),
    ])

    engine = WorkflowEngine()
    workflow = await engine.execute(request)

    assert workflow.intent == WorkflowIntent.CANCELLATION_REQUEST
    assert workflow.status == WorkflowStatus.PENDING_APPROVAL
    assert workflow.policy_result.decision == "REQUIRES_APPROVAL"
    assert workflow.policy_result.approval_tier == "manager"


@pytest.mark.asyncio
async def test_workflow_no_order_id_fails(mock_tools):
    """Test workflow fails when no order ID can be extracted."""
    mock_registry, responses, mock_approval, mock_audit = mock_tools
    
    request = ResolutionRequest(
        request_id="req-test-no-order",
        user_request="I want a refund please",
        # No order_id provided, and none in request text
    )
    
    engine = WorkflowEngine()
    workflow = await engine.execute(request)

    # Should still create workflow but fail at investigation step
    assert workflow.intent == WorkflowIntent.REFUND_REQUEST
    assert workflow.status == WorkflowStatus.FAILED
    assert any("No order ID" in e for e in workflow.errors)


@pytest.mark.asyncio
async def test_build_response(workflow_engine, sample_resolution_request):
    """Test response building from workflow."""
    # Create a completed workflow
    from app.workflows.models import ResolutionWorkflow, WorkflowStatus, WorkflowIntent
    from datetime import datetime
    
    workflow = ResolutionWorkflow(
        id="test-workflow-id",
        request_id="req-test-123",
        user_request="Order 10482 hasn't arrived and I want a refund",
        intent=WorkflowIntent.REFUND_REQUEST,
        status=WorkflowStatus.COMPLETED,
        order_id="10482",
        order_number="10482",
        final_status="completed",
        completed_at=datetime.utcnow(),
    )
    
    response = workflow_engine.build_response(workflow)
    
    assert isinstance(response, ResolutionResponse)
    assert response.workflow_id == workflow.id
    assert response.request_id == workflow.request_id
    assert response.status == workflow.status
    assert response.final_message is not None
    assert len(response.final_message) > 0