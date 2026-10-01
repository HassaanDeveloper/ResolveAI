import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from app.tools.get_order import GetOrderTool, GetOrderInput


def make_async_mock(return_value):
    """Create an async mock that returns the given value when awaited."""
    mock = AsyncMock()
    mock.return_value = return_value
    return mock


@pytest.mark.asyncio
async def test_get_order_success(mock_supabase, sample_order, sample_customer):
    """Test successful order retrieval."""
    # Setup mock chain for orders table
    orders_mock = MagicMock()
    orders_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_order
    
    # Setup mock chain for customers table
    customers_mock = MagicMock()
    customers_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_customer
    
    # Configure table() to return different mocks based on table name
    def table_side_effect(table_name):
        if table_name == "orders":
            return orders_mock
        elif table_name == "customers":
            return customers_mock
        return MagicMock()
    
    mock_supabase.table.side_effect = table_side_effect

    tool = GetOrderTool()
    
    # Mock the circuit breaker to bypass it and call the function directly
    with patch("app.tools.get_order.supabase_circuit_breaker") as mock_cb:
        async def mock_call(func):
            return await func()
        mock_cb.call = mock_call
        result = await tool.execute(GetOrderInput(order_id="10482"))

    assert result.success is True
    assert result.data is not None
    assert result.data["order"]["order_number"] == "10482"
    assert result.data["order"]["customer_name"] == "Sarah Mitchell"
    assert result.data["order"]["total_amount"] == Decimal("74.99")


@pytest.mark.asyncio
async def test_get_order_not_found(mock_supabase, sample_order, sample_customer):
    """Test order not found."""
    # Setup mock chain for orders table returning None
    orders_mock = MagicMock()
    orders_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
    
    def table_side_effect(table_name):
        if table_name == "orders":
            return orders_mock
        return MagicMock()
    
    mock_supabase.table.side_effect = table_side_effect

    tool = GetOrderTool()
    
    with patch("app.tools.get_order.supabase_circuit_breaker") as mock_cb:
        async def mock_call(func):
            return await func()
        mock_cb.call = mock_call
        result = await tool.execute(GetOrderInput(order_id="99999"))

    assert result.success is False
    assert result.error.error_code == "NOT_FOUND"
    assert "not found" in result.error.message.lower()


@pytest.mark.asyncio
async def test_get_order_execution_error(mock_supabase):
    """Test execution error handling."""
    orders_mock = MagicMock()
    orders_mock.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")
    
    def table_side_effect(table_name):
        if table_name == "orders":
            return orders_mock
        return MagicMock()
    
    mock_supabase.table.side_effect = table_side_effect

    tool = GetOrderTool()
    
    with patch("app.tools.get_order.supabase_circuit_breaker") as mock_cb:
        # Make circuit breaker call raise the exception
        mock_cb.call = AsyncMock(side_effect=Exception("DB error"))
        
        result = await tool.execute(GetOrderInput(order_id="10482"))

    assert result.success is False
    assert result.error.error_code == "EXECUTION_ERROR"