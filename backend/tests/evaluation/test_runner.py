import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from evaluation.runner import run_evaluation
from evaluation.models import scenario_store
from app.workflows.models import ResolutionRequest
from app.audit.models import AuditEvent


# Load all scenarios
import evaluation.scenarios.refund_scenarios
import evaluation.scenarios.cancellation_scenarios
import evaluation.scenarios.escalation_shipping_scenarios


@pytest.fixture
def mock_audit_service():
    """Mock the audit service."""
    with patch("app.workflows.engine.audit_service") as mock:
        # Mock record_event_simple to return a mock AuditEvent
        mock_audit_event = MagicMock()
        mock_audit_event.id = "test-audit-id"
        mock_audit_event.request_id = "test-request-id"
        mock_audit_event.event_type = "test_event"
        mock_audit_event.event_data = {}
        mock_audit_event.created_at = "2025-01-01T00:00:00+00:00"
        
        mock.record_event_simple = AsyncMock(return_value=mock_audit_event)
        mock.record_event = AsyncMock(return_value=MagicMock(
            id="test-audit-id",
            request_id="test-request-id",
            event_type="test_event",
            event_data={},
            created_at="2025-01-01T00:00:00+00:00"
        ))
        yield mock


@pytest.mark.asyncio
async def test_evaluation_scenarios_exist():
    """Test that scenarios are loaded."""
    scenarios = scenario_store.get_all()
    assert len(scenarios) >= 12
    
    # Check categories
    categories = set(s.category for s in scenario_store.get_all())
    assert "refund" in categories
    assert "cancellation" in categories
    assert "escalation" in categories
    assert "shipping_inquiry" in categories


@pytest.mark.asyncio
async def test_run_single_scenario(mock_audit_service):
    """Test running a single evaluation scenario."""
    scenarios = scenario_store.get_all()
    refund_scenario = next(s for s in scenario_store.get_all() if s.id == "refund_001")
    
    from evaluation.runner import run_evaluation
    result = await run_evaluation(refund_scenario)
    
    assert result.scenario_id == "refund_001"
    assert result.scenario_name == "Delayed shipment refund - auto approve"
    assert "task_success" in result.metrics
    assert "tool_selection_accuracy" in result.metrics


@pytest.mark.asyncio
async def test_all_scenarios_categories():
    """Test all scenario categories are represented."""
    scenarios = scenario_store.get_all()
    categories = {}
    for s in scenario_store.get_all():
        if s.category not in categories:
            categories[s.category] = 0
        categories[s.category] += 1
    
    assert categories["refund"] >= 5
    assert categories["cancellation"] >= 3
    assert categories["escalation"] >= 2
    assert categories["shipping_inquiry"] >= 2