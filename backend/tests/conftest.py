import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    with patch("app.services.database.get_supabase_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_order():
    return {
        "id": "test-order-uuid-1",
        "order_number": "10482",
        "customer_id": "test-customer-uuid-1",
        "status": "shipped",
        "total_amount": 74.99,
        "currency": "USD",
        "created_at": "2025-08-01T10:00:00+00:00",
        "updated_at": "2025-08-01T10:00:00+00:00",
    }


@pytest.fixture
def sample_customer():
    return {
        "id": "test-customer-uuid-1",
        "external_customer_id": "CUST-001",
        "name": "Sarah Mitchell",
        "email": "sarah.mitchell@email.com",
        "account_status": "active",
        "created_at": "2025-01-01T10:00:00+00:00",
    }


@pytest.fixture
def sample_shipment():
    return {
        "id": "test-shipment-uuid-1",
        "order_id": "test-order-uuid-1",
        "carrier": "FedEx",
        "tracking_number": "FX123456789US",
        "status": "delayed",
        "estimated_delivery_date": "2025-08-15",
        "delivered_at": None,
        "updated_at": "2025-08-20T10:00:00+00:00",
    }