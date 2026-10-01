import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from app.tools.calculate_refund import CalculateRefundTool, CalculateRefundInput


def setup_calculate_refund_mocks(mock_supabase, sample_order, sample_shipment, existing_refunds=None):
    """Helper to set up mocks for calculate_refund tests with proper table differentiation."""
    orders_mock = MagicMock()
    orders_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    
    shipments_mock = MagicMock()
    shipments_mock.select.return_value.eq.return_value.execute.return_value.data = [sample_shipment]
    
    refunds_mock = MagicMock()
    refunds_mock.select.return_value.eq.return_value.execute.return_value.data = existing_refunds or []
    
    def table_side_effect(table_name):
        if table_name == "orders":
            return orders_mock
        elif table_name == "shipments":
            return shipments_mock
        elif table_name == "refunds":
            return refunds_mock
        return MagicMock()
    
    mock_supabase.table.side_effect = table_side_effect


@pytest.mark.asyncio
async def test_calculate_refund_delayed_eligible(mock_supabase, sample_order, sample_shipment):
    """Test refund calculation for delayed shipment (eligible)."""
    from datetime import datetime, timezone, timedelta
    # Use an estimated delivery date 19 days ago
    past_date = (datetime.now(timezone.utc) - timedelta(days=19)).date().isoformat()
    
    # Create modified copies to avoid fixture mutation issues
    order_data = {**sample_order, "status": "shipped"}
    shipment_data = {**sample_shipment, "status": "delayed", "estimated_delivery_date": past_date}
    
    setup_calculate_refund_mocks(mock_supabase, order_data, shipment_data, existing_refunds=[])

    tool = CalculateRefundTool()
    result = await tool.execute(CalculateRefundInput(order_id="10482"))

    assert result.success is True
    assert result.data is not None
    assert result.data["calculation"]["eligible_amount"] == Decimal("74.99")
    assert "delayed" in result.data["calculation"]["eligibility_reason"].lower()


@pytest.mark.asyncio
async def test_calculate_refund_delivered_within_30_days(mock_supabase, sample_order, sample_shipment):
    """Test refund calculation for delivered order within 30 days."""
    from datetime import datetime, timezone, timedelta
    # Use a date 10 days ago from now
    recent_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    
    # Create modified copies to avoid fixture mutation issues
    order_data = {**sample_order, "status": "delivered"}
    shipment_data = {**sample_shipment, "status": "delivered", "delivered_at": recent_date}
    
    setup_calculate_refund_mocks(mock_supabase, order_data, shipment_data, existing_refunds=[])

    tool = CalculateRefundTool()
    result = await tool.execute(CalculateRefundInput(order_id="10482"))

    assert result.success is True
    assert result.data["calculation"]["eligible_amount"] == Decimal("74.99")
    assert "within 30-day" in result.data["calculation"]["eligibility_reason"]


@pytest.mark.asyncio
async def test_calculate_refund_delivered_outside_30_days(mock_supabase, sample_order, sample_shipment):
    """Test refund calculation for delivered order outside 30 days."""
    from datetime import datetime, timezone, timedelta
    # Use a date 60 days ago
    old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    
    # Create modified copies to avoid fixture mutation issues
    order_data = {**sample_order, "status": "delivered"}
    shipment_data = {**sample_shipment, "status": "delivered", "delivered_at": old_date}
    
    setup_calculate_refund_mocks(mock_supabase, order_data, shipment_data, existing_refunds=[])

    tool = CalculateRefundTool()
    result = await tool.execute(CalculateRefundInput(order_id="10482"))

    assert result.success is True
    assert result.data["calculation"]["eligible_amount"] == Decimal("0")
    assert "outside 30-day" in result.data["calculation"]["eligibility_reason"]


@pytest.mark.asyncio
async def test_calculate_refund_already_refunded(mock_supabase, sample_order, sample_shipment):
    """Test refund calculation for already refunded order."""
    sample_order["status"] = "refunded"
    
    setup_calculate_refund_mocks(mock_supabase, sample_order, sample_shipment, existing_refunds=[{"amount": 74.99, "status": "completed"}])

    tool = CalculateRefundTool()
    result = await tool.execute(CalculateRefundInput(order_id="10482"))

    assert result.success is True
    assert result.data["calculation"]["eligible_amount"] == Decimal("0")
    assert "already fully refunded" in result.data["calculation"]["eligibility_reason"].lower()


@pytest.mark.asyncio
async def test_calculate_refund_shipped_not_delayed(mock_supabase, sample_order, sample_shipment):
    """Test refund calculation for shipped but not delayed."""
    from datetime import datetime, timezone, timedelta
    # Use a future estimated delivery date
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).date().isoformat()
    
    # Create modified copies to avoid fixture mutation issues
    order_data = {**sample_order, "status": "shipped"}
    shipment_data = {**sample_shipment, "status": "in_transit", "estimated_delivery_date": future_date}
    
    setup_calculate_refund_mocks(mock_supabase, order_data, shipment_data, existing_refunds=[])

    tool = CalculateRefundTool()
    result = await tool.execute(CalculateRefundInput(order_id="10482"))

    assert result.success is True
    assert result.data["calculation"]["eligible_amount"] == Decimal("0")
    assert "not eligible" in result.data["calculation"]["eligibility_reason"].lower()