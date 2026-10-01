import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from app.tools.issue_refund import IssueRefundTool, IssueRefundInput
from app.tools.cancel_order import CancelOrderTool, CancelOrderInput
from app.tools.create_escalation import CreateEscalationTool, CreateEscalationInput


@pytest.fixture
def mock_idempotency_service():
    """Mock the idempotency service."""
    with patch("app.tools.issue_refund.idempotency_service") as mock_issue, \
         patch("app.tools.cancel_order.idempotency_service") as mock_cancel:
        # Default mock for check_idempotency (returns None = no existing operation)
        mock_issue.check_idempotency = AsyncMock(return_value=None)
        mock_cancel.check_idempotency = AsyncMock(return_value=None)
        # Default mock for reserve_operation (returns True = reserved)
        mock_issue.reserve_operation = AsyncMock(return_value=True)
        mock_cancel.reserve_operation = AsyncMock(return_value=True)
        # Default mocks for marking operations
        mock_issue.mark_executing = AsyncMock()
        mock_issue.mark_executed = AsyncMock()
        mock_issue.mark_failed = AsyncMock()
        mock_cancel.mark_executing = AsyncMock()
        mock_cancel.mark_executed = AsyncMock()
        mock_cancel.mark_failed = AsyncMock()
        
        yield mock_issue, mock_cancel


@pytest.mark.asyncio
async def test_issue_refund_success_idempotent(mock_supabase, sample_order, mock_idempotency_service):
    """Test successful refund with idempotency."""
    mock_issue, mock_cancel = mock_idempotency_service
    operation_id = "refund-order-10482-74.99"
    
    # Setup Supabase mocks
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    # No refund row exists yet for this operation_id (idempotency pre-check)
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "refund-uuid-1"}]
    mock_supabase.table.return_value.upsert.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

    tool = IssueRefundTool()
    result = await tool.execute(IssueRefundInput(
        order_id="10482",
        amount=Decimal("74.99"),
        operation_id=operation_id,
        reason="Delayed shipment"
    ))

    assert result.success is True
    assert result.data["result"]["success"] is True
    assert result.data["result"]["operation_id"] == operation_id
    assert result.data["result"]["status"] == "completed"


@pytest.mark.asyncio
async def test_issue_refund_idempotent_duplicate(mock_supabase, sample_order, mock_idempotency_service):
    """Test idempotent behavior - duplicate operation returns previous result."""
    mock_issue, mock_cancel = mock_idempotency_service
    operation_id = "refund-order-10482-74.99"
    
    # Existing completed operation
    from app.reliability.models import OperationResult
    mock_issue.check_idempotency = AsyncMock(return_value=OperationResult(
        success=True,
        data={"refund_id": "refund-uuid-1", "currency": "USD", "processed_at": "2025-08-25T10:00:00+00:00"},
        idempotent=True
    ))
    
    # Order lookup
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order

    tool = IssueRefundTool()
    result = await tool.execute(IssueRefundInput(
        order_id="10482",
        amount=Decimal("74.99"),
        operation_id=operation_id,
        reason="Delayed shipment"
    ))

    assert result.success is True
    assert result.data["result"]["status"] == "duplicate"
    assert "already processed" in result.data["result"]["message"].lower()


@pytest.mark.asyncio
async def test_issue_refund_exceeds_order_total(mock_supabase, sample_order, mock_idempotency_service):
    """Test refund amount validation."""
    mock_issue, mock_cancel = mock_idempotency_service
    mock_issue.check_idempotency = AsyncMock(return_value=None)
    mock_issue.reserve_operation = AsyncMock(return_value=True)
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    tool = IssueRefundTool()
    result = await tool.execute(IssueRefundInput(
        order_id="10482",
        amount=Decimal("1000.00"),  # Exceeds order total of 74.99
        operation_id="refund-order-10482-1000",
        reason="Test"
    ))

    assert result.success is False
    assert result.error.error_code == "VALIDATION_ERROR"
    assert "exceeds order total" in result.error.message.lower()


@pytest.mark.asyncio
async def test_cancel_order_success_not_shipped(mock_supabase, sample_order, mock_idempotency_service):
    """Test successful cancellation for non-shipped order."""
    mock_issue, mock_cancel = mock_idempotency_service
    mock_cancel.check_idempotency = AsyncMock(return_value=None)
    mock_cancel.reserve_operation = AsyncMock(return_value=True)
    
    sample_order["status"] = "processing"
    
    # Create separate mocks for different tables
    orders_mock = MagicMock()
    orders_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    orders_mock.update.return_value.eq.return_value.execute.return_value.data = []
    
    shipments_mock = MagicMock()
    shipments_mock.select.return_value.eq.return_value.execute.return_value.data = [{"status": "pending"}]  # not shipped
    
    def table_side_effect(table_name):
        if table_name == "orders":
            return orders_mock
        elif table_name == "shipments":
            return shipments_mock
        return MagicMock()
    
    mock_supabase.table.side_effect = table_side_effect

    tool = CancelOrderTool()
    result = await tool.execute(CancelOrderInput(
        order_id="10482",
        operation_id="cancel-order-10482",
        reason="Customer requested"
    ))

    assert result.success is True
    assert result.data["result"]["success"] is True
    assert result.data["result"]["status"] == "cancelled"
    assert result.data["result"]["requires_approval"] is False


@pytest.mark.asyncio
async def test_cancel_order_shipped_requires_approval(mock_supabase, sample_order, mock_idempotency_service):
    """Test cancellation for shipped order requires approval."""
    mock_issue, mock_cancel = mock_idempotency_service
    mock_cancel.check_idempotency = AsyncMock(return_value=None)
    mock_cancel.reserve_operation = AsyncMock(return_value=True)
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"status": "shipped"}]

    tool = CancelOrderTool()
    result = await tool.execute(CancelOrderInput(
        order_id="10482",
        operation_id="cancel-order-10482",
        reason="Customer requested"
    ))

    assert result.success is True
    assert result.data["result"]["requires_approval"] is True


@pytest.mark.asyncio
async def test_cancel_order_delivered_fails(mock_supabase, sample_order, mock_idempotency_service):
    """Test cancellation fails for delivered order."""
    mock_issue, mock_cancel = mock_idempotency_service
    mock_cancel.check_idempotency = AsyncMock(return_value=None)
    mock_cancel.reserve_operation = AsyncMock(return_value=True)
    
    sample_order["status"] = "delivered"
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"status": "delivered"}]

    tool = CancelOrderTool()
    result = await tool.execute(CancelOrderInput(
        order_id="10482",
        operation_id="cancel-order-10482",
        reason="Customer requested"
    ))

    assert result.success is False
    assert result.error.error_code == "VALIDATION_ERROR"
    assert "delivered" in result.error.message.lower()


@pytest.mark.asyncio
async def test_create_escalation_success():
    """Test successful escalation creation."""
    # Mock the database service
    import app.services.database as database_module
    original_get_supabase = database_module.get_supabase_client
    
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value.data = []
    
    database_module.get_supabase_client = lambda: mock_client
    
    try:
        tool = CreateEscalationTool()
        result = await tool.execute(CreateEscalationInput(
            reason="Policy exception request",
            context={"order_id": "10482", "request_id": "req-123"},
            priority="high"
        ))
        
        assert result.success is True
        assert result.data["result"]["success"] is True
        assert result.data["result"]["escalation_id"].startswith("esc-")
        assert result.data["result"]["status"] == "open"
    finally:
        database_module.get_supabase_client = original_get_supabase
        database_module.reset_supabase_client()