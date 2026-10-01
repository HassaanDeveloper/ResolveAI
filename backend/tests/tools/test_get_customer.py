import pytest
from app.tools.get_customer import GetCustomerTool, GetCustomerInput


@pytest.mark.asyncio
async def test_get_customer_success(mock_supabase, sample_customer):
    """Test successful customer retrieval."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = sample_customer

    tool = GetCustomerTool()
    result = await tool.execute(GetCustomerInput(customer_id="CUST-001"))

    assert result.success is True
    assert result.data is not None
    assert result.data["customer"]["external_customer_id"] == "CUST-001"
    assert result.data["customer"]["name"] == "Sarah Mitchell"
    assert result.data["customer"]["email"] == "sarah.mitchell@email.com"


@pytest.mark.asyncio
async def test_get_customer_not_found(mock_supabase):
    """Test customer not found."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    tool = GetCustomerTool()
    result = await tool.execute(GetCustomerInput(customer_id="CUST-999"))

    assert result.success is False
    assert result.error.error_code == "NOT_FOUND"