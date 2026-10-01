"""
Synthetic test data for real integration evaluation.
These are dedicated test records with identifiable test IDs.
Uses business keys for lookups since DB generates UUIDs.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta

# Test namespace prefix for all test records
TEST_NAMESPACE = "eval-test-"

# Synthetic test customers (DB generates UUID at runtime)
TEST_CUSTOMERS = [
    {
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "name": "Eval Test Customer One",
        "email": "eval-test-001@example.com",
        "account_status": "active",
    },
    {
        "external_customer_id": f"{TEST_NAMESPACE}CUST-002",
        "name": "Eval Test Customer Two",
        "email": "eval-test-002@example.com",
        "account_status": "active",
    },
    {
        "external_customer_id": f"{TEST_NAMESPACE}CUST-003",
        "name": "Eval Test Customer Three",
        "email": "eval-test-003@example.com",
        "account_status": "active",
    },
]

# Synthetic test orders with various states for different scenarios
# DB generates UUID at runtime; order_number is the business key
# Use float for total_amount to ensure JSON serializable for Supabase
# id = business key (order_number) for static data lookups
TEST_ORDERS = [
    # Delayed shipment, low value (<= $50) - should auto-approve
    {
        "id": f"{TEST_NAMESPACE}10001",
        "order_number": f"{TEST_NAMESPACE}10001",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "status": "shipped",
        "total_amount": 49.99,
        "currency": "USD",
    },
    # Delayed shipment, high value (> $50, <= $200) - requires manager approval
    {
        "id": f"{TEST_NAMESPACE}10002",
        "order_number": f"{TEST_NAMESPACE}10002",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "status": "shipped",
        "total_amount": 150.00,
        "currency": "USD",
    },
    # Failed shipment - carrier loss
    {
        "id": f"{TEST_NAMESPACE}10003",
        "order_number": f"{TEST_NAMESPACE}10003",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-002",
        "status": "shipped",
        "total_amount": 75.00,
        "currency": "USD",
    },
    # Delivered outside window - should be denied
    {
        "id": f"{TEST_NAMESPACE}10004",
        "order_number": f"{TEST_NAMESPACE}10004",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-002",
        "status": "delivered",
        "total_amount": 89.99,
        "currency": "USD",
    },
    # Processing (not shipped) - cancellation should auto-approve
    {
        "id": f"{TEST_NAMESPACE}10005",
        "order_number": f"{TEST_NAMESPACE}10005",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-003",
        "status": "processing",
        "total_amount": 120.00,
        "currency": "USD",
    },
    # Processing (not shipped) - cancellation should auto-approve (fresh fixture for tool_002 re-run)
    {
        "id": f"{TEST_NAMESPACE}10011",
        "order_number": f"{TEST_NAMESPACE}10011",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-003",
        "status": "processing",
        "total_amount": 120.00,
        "currency": "USD",
    },
    # Shipped - cancellation requires approval
    {
        "id": f"{TEST_NAMESPACE}10006",
        "order_number": f"{TEST_NAMESPACE}10006",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-003",
        "status": "shipped",
        "total_amount": 200.00,
        "currency": "USD",
    },
    # Delayed shipment, low value (<= $50) - should auto-approve (fresh fixture for isolation)
    {
        "id": f"{TEST_NAMESPACE}10007",
        "order_number": f"{TEST_NAMESPACE}10007",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "status": "shipped",
        "total_amount": 49.99,
        "currency": "USD",
    },
    # Delayed shipment, low value (<= $50) - should auto-approve (fresh fixture for idempotency test)
    {
        "id": f"{TEST_NAMESPACE}10008",
        "order_number": f"{TEST_NAMESPACE}10008",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "status": "shipped",
        "total_amount": 49.99,
        "currency": "USD",
    },
    # Delayed shipment, low value (<= $50) - should auto-approve (fresh fixture for tool_001)
    {
        "id": f"{TEST_NAMESPACE}10009",
        "order_number": f"{TEST_NAMESPACE}10009",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "status": "shipped",
        "total_amount": 49.99,
        "currency": "USD",
    },
    # Delayed shipment, low value (<= $50) - should auto-approve (fresh fixture for tool_001 re-run)
    {
        "id": f"{TEST_NAMESPACE}10010",
        "order_number": f"{TEST_NAMESPACE}10010",
        "external_customer_id": f"{TEST_NAMESPACE}CUST-001",
        "status": "shipped",
        "total_amount": 49.99,
        "currency": "USD",
    },
]

# Synthetic test shipments
TEST_SHIPMENTS = [
    # Delayed > 7 days for order 10001
    {
        "id": f"{TEST_NAMESPACE}ship-001",
        "order_number": f"{TEST_NAMESPACE}10001",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10001",
        "status": "delayed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat(),
        "delivered_at": None,
    },
    # Delayed > 7 days for order 10002
    {
        "id": f"{TEST_NAMESPACE}ship-002",
        "order_number": f"{TEST_NAMESPACE}10002",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10002",
        "status": "delayed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat(),
        "delivered_at": None,
    },
    # Failed shipment for order 10003
    {
        "id": f"{TEST_NAMESPACE}ship-003",
        "order_number": f"{TEST_NAMESPACE}10003",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10003",
        "status": "failed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat(),
        "delivered_at": None,
    },
    # Delivered 45 days ago for order 10004
    {
        "id": f"{TEST_NAMESPACE}ship-004",
        "order_number": f"{TEST_NAMESPACE}10004",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10004",
        "status": "delivered",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=50)).date().isoformat(),
        "delivered_at": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
    },
    # Pending for order 10005
    {
        "id": f"{TEST_NAMESPACE}ship-005",
        "order_number": f"{TEST_NAMESPACE}10005",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10005",
        "status": "pending",
        "estimated_delivery_date": (datetime.now(timezone.utc) + timedelta(days=5)).date().isoformat(),
        "delivered_at": None,
    },
    # In transit for order 10006
    {
        "id": f"{TEST_NAMESPACE}ship-006",
        "order_number": f"{TEST_NAMESPACE}10006",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10006",
        "status": "in_transit",
        "estimated_delivery_date": (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat(),
        "delivered_at": None,
    },
    # Delayed > 7 days for order 10007
    {
        "id": f"{TEST_NAMESPACE}ship-007",
        "order_number": f"{TEST_NAMESPACE}10007",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10007",
        "status": "delayed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat(),
        "delivered_at": None,
    },
    # Delayed > 7 days for order 10008
    {
        "id": f"{TEST_NAMESPACE}ship-008",
        "order_number": f"{TEST_NAMESPACE}10008",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10008",
        "status": "delayed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat(),
        "delivered_at": None,
    },
    # Delayed > 7 days for order 10009
    {
        "id": f"{TEST_NAMESPACE}ship-009",
        "order_number": f"{TEST_NAMESPACE}10009",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10009",
        "status": "delayed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat(),
        "delivered_at": None,
    },
    # Delayed > 7 days for order 10010
    {
        "id": f"{TEST_NAMESPACE}ship-010",
        "order_number": f"{TEST_NAMESPACE}10010",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10010",
        "status": "delayed",
        "estimated_delivery_date": (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat(),
        "delivered_at": None,
    },
    # Pending for order 10011
    {
        "id": f"{TEST_NAMESPACE}ship-011",
        "order_number": f"{TEST_NAMESPACE}10011",
        "carrier": "TestCarrier",
        "tracking_number": f"{TEST_NAMESPACE}TX10011",
        "status": "pending",
        "estimated_delivery_date": (datetime.now(timezone.utc) + timedelta(days=5)).date().isoformat(),
        "delivered_at": None,
    },
]

# Test refund records (pre-existing for idempotency/denial tests)
TEST_REFUNDS = [
    {
        "order_number": f"{TEST_NAMESPACE}10004",  # Already refunded order
        "amount": 89.99,
        "currency": "USD",
        "status": "completed",
        "operation_id": f"{TEST_NAMESPACE}refund-10004-89.99",
        "processed_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    },
]

# Test approval requests (for approval transition tests)
TEST_APPROVALS = [
    {
        "resolution_id": f"{TEST_NAMESPACE}resolution-001",  # Placeholder, will be set at runtime
        "action_type": "issue_refund",
        "action_payload": {"order_id": f"{TEST_NAMESPACE}10002", "amount": "150.00"},
        "reason": "Refund exceeds auto-approve threshold",
        "policy_rule": "refund_manager_approval",
        "risk_level": "medium",
        "status": "pending",
    },
]

# Idempotency test operation IDs
IDEMPOTENCY_TEST_OPERATIONS = {
    "refund_duplicate": f"{TEST_NAMESPACE}refund-duplicate-10001-49.99",
    "cancel_duplicate": f"{TEST_NAMESPACE}cancel-duplicate-10005",
}

# Runtime-resolved IDs (populated during setup)
_RUNTIME_IDS = {
    "customers": {},  # external_customer_id -> uuid
    "orders": {},     # order_number -> uuid
    "shipments": {},  # tracking_number -> uuid
}

def _get_customer_id(client, external_customer_id: str) -> str:
    """Get customer UUID by external_customer_id."""
    if external_customer_id in _RUNTIME_IDS["customers"]:
        return _RUNTIME_IDS["customers"][external_customer_id]
    result = client.table("customers").select("id").eq("external_customer_id", external_customer_id).single().execute()
    if result.data:
        _RUNTIME_IDS["customers"][external_customer_id] = result.data["id"]
        return result.data["id"]
    return None

def _get_order_id(client, order_number: str) -> str:
    """Get order UUID by order_number."""
    if order_number in _RUNTIME_IDS["orders"]:
        return _RUNTIME_IDS["orders"][order_number]
    result = client.table("orders").select("id").eq("order_number", order_number).single().execute()
    if result.data:
        _RUNTIME_IDS["orders"][order_number] = result.data["id"]
        return result.data["id"]
    return None

def _get_shipment_id(client, tracking_number: str) -> str:
    """Get shipment UUID by tracking_number."""
    if tracking_number in _RUNTIME_IDS["shipments"]:
        return _RUNTIME_IDS["shipments"][tracking_number]
    result = client.table("shipments").select("id").eq("tracking_number", tracking_number).single().execute()
    if result.data:
        _RUNTIME_IDS["shipments"][tracking_number] = result.data["id"]
        return result.data["id"]
    return None

def get_test_order_by_number(order_number: str):
    """Get test order by order_number (business key). Returns order dict with DB-generated UUID if available."""
    # Check runtime cache first for DB-generated UUID
    if order_number in _RUNTIME_IDS["orders"]:
        order_data = _get_test_order_by_number_legacy(order_number)
        if order_data:
            # Return a copy with the DB-generated UUID
            result = order_data.copy()
            result["id"] = _RUNTIME_IDS["orders"][order_number]
            return result
    # Fallback to static test data
    return _get_test_order_by_number_legacy(order_number)

def _get_test_order_by_number_legacy(order_number: str):
    """Get test order by order_number from static test data (no DB UUID)."""
    for order in TEST_ORDERS:
        if order["order_number"] == order_number:
            return order
    return None

def get_test_shipment_by_order_id(order_number: str):
    """Get test shipment by order_number (business key). Returns shipment dict with DB-generated UUID if available."""
    # Check runtime cache first for DB-generated UUID
    if order_number in _RUNTIME_IDS["orders"]:
        order_id = _RUNTIME_IDS["orders"][order_number]
        # Find shipment by order_number
        for shipment in TEST_SHIPMENTS:
            if shipment["order_number"] == order_number:
                result = shipment.copy()
                # Add DB-generated UUIDs if available
                if shipment["tracking_number"] in _RUNTIME_IDS["shipments"]:
                    result["id"] = _RUNTIME_IDS["shipments"][shipment["tracking_number"]]
                result["order_id"] = order_id
                return result
    # Fallback to static test data
    for shipment in TEST_SHIPMENTS:
        if shipment["order_number"] == order_number:
            return shipment
    return None

def get_test_customer_by_external_id(external_id: str):
    """Get test customer by external_customer_id. Returns customer dict with DB-generated UUID if available."""
    if external_id in _RUNTIME_IDS["customers"]:
        customer_data = _get_test_customer_by_external_id_legacy(external_id)
        if customer_data:
            result = customer_data.copy()
            result["id"] = _RUNTIME_IDS["customers"][external_id]
            return result
    return _get_test_customer_by_external_id_legacy(external_id)

def _get_test_customer_by_external_id_legacy(external_id: str):
    """Get test customer by external_customer_id from static test data."""
    for customer in TEST_CUSTOMERS:
        if customer["external_customer_id"] == external_id:
            return customer
    return None