import pytest
from app.tools.get_shipping_status import GetShippingStatusTool, GetShippingStatusInput


@pytest.mark.asyncio
async def test_get_shipping_status_success(mock_supabase, sample_order, sample_shipment):
    """Test successful shipping status retrieval."""
    # First call returns order
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    # Second call returns shipment
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [sample_shipment]

    tool = GetShippingStatusTool()
    result = await tool.execute(GetShippingStatusInput(order_id="10482"))

    assert result.success is True
    assert result.data is not None
    assert result.data["shipment"]["tracking_number"] == "FX123456789US"
    assert result.data["shipment"]["status"] == "delayed"
    assert result.data["shipment"]["carrier"] == "FedEx"


@pytest.mark.asyncio
async def test_get_shipping_status_order_not_found(mock_supabase):
    """Test order not found."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    tool = GetShippingStatusTool()
    result = await tool.execute(GetShippingStatusInput(order_id="99999"))

    assert result.success is False
    assert result.error.error_code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_shipping_status_no_shipment(mock_supabase, sample_order):
    """Test no shipment found for order."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    tool = GetShippingStatusTool()
    result = await tool.execute(GetShippingStatusInput(order_id="10482"))

    assert result.success is False
    assert result.error.error_code == "NOT_FOUND"