import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.tools.search_company_policy import SearchCompanyPolicyTool, SearchCompanyPolicyInput
from app.rag.retrieval.models import Evidence


@pytest.fixture
def mock_retrieval_service():
    """Mock the retrieval service to avoid needing real API keys."""
    with patch("app.tools.search_company_policy.retrieval_service") as mock:
        yield mock


@pytest.mark.asyncio
async def test_search_company_policy_delayed_shipment(mock_retrieval_service):
    """Test search for delayed shipment refund policy."""
    # Mock retrieval service response
    mock_evidence = [
        Evidence(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="Refund Policy v2.1",
            section="Delayed Shipment Refunds",
            source="internal-policy",
            version="2.1",
            content="Customers are eligible for a full refund if a shipment is delayed beyond the estimated delivery date by more than 7 business days and the package has not been delivered.",
            relevance_score=0.92,
            metadata={}
        ),
        Evidence(
            chunk_id="chunk-2",
            document_id="doc-1",
            document_name="Refund Policy v2.1",
            section="Refund Approval Thresholds",
            source="internal-policy",
            version="2.1",
            content="Refund approval matrix: Amount ≤ $100 with valid eligibility → AUTO_APPROVE.",
            relevance_score=0.85,
            metadata={}
        ),
    ]
    
    mock_response = MagicMock()
    mock_response.results = mock_evidence
    mock_response.error = None
    
    mock_retrieval_service.search_company_policy = AsyncMock(return_value=mock_response)
    
    tool = SearchCompanyPolicyTool()
    result = await tool.execute(SearchCompanyPolicyInput(
        query="delayed shipment refund eligibility",
        max_results=3
    ))

    assert result.success is True
    assert result.data is not None
    assert len(result.data["results"]) == 2
    # Should find the delayed shipment refund policy
    found = any("delayed" in r["content"].lower() for r in result.data["results"])
    assert found


@pytest.mark.asyncio
async def test_search_company_policy_approval_threshold(mock_retrieval_service):
    """Test search for approval thresholds."""
    mock_evidence = [
        Evidence(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="Refund Approval Matrix",
            section="Approval Levels",
            source="internal-policy",
            version="1.0",
            content="Tier 1 (Auto): ≤$100, standard eligibility met. Tier 2 (Manager): $100-$500.",
            relevance_score=0.90,
            metadata={}
        ),
    ]
    
    mock_response = MagicMock()
    mock_response.results = mock_evidence
    mock_response.error = None
    
    mock_retrieval_service.search_company_policy = AsyncMock(return_value=mock_response)
    
    tool = SearchCompanyPolicyTool()
    result = await tool.execute(SearchCompanyPolicyInput(
        query="refund approval threshold $100 manager",
        max_results=3
    ))

    assert result.success is True
    assert result.data is not None
    assert len(result.data["results"]) == 1
    found = any(("approval" in r["content"].lower() or "tier" in r["content"].lower()) and ("100" in r["content"] or "$100" in r["content"]) for r in result.data["results"])
    assert found


@pytest.mark.asyncio
async def test_search_company_policy_cancellation_shipped(mock_retrieval_service):
    """Test search for shipped order cancellation."""
    mock_evidence = [
        Evidence(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="Order Cancellation Policy v1.3",
            section="Post-Shipment Cancellations",
            source="internal-policy",
            version="1.3",
            content="Orders that have already shipped cannot be cancelled through standard process. Customer must request escalation. If shipment is delayed > 14 days, cancellation may be approved with return authorization.",
            relevance_score=0.88,
            metadata={}
        ),
    ]
    
    mock_response = MagicMock()
    mock_response.results = mock_evidence
    mock_response.error = None
    
    mock_retrieval_service.search_company_policy = AsyncMock(return_value=mock_response)
    
    tool = SearchCompanyPolicyTool()
    result = await tool.execute(SearchCompanyPolicyInput(
        query="cancellation after shipment escalation",
        max_results=3
    ))

    assert result.success is True
    assert result.data is not None
    assert len(result.data["results"]) == 1
    found = any("shipped" in r["content"].lower() and "escalat" in r["content"].lower() for r in result.data["results"])
    assert found


@pytest.mark.asyncio
async def test_search_company_policy_no_results(mock_retrieval_service):
    """Test search with no matching results."""
    mock_response = MagicMock()
    mock_response.results = []
    mock_response.error = None
    
    mock_retrieval_service.search_company_policy = AsyncMock(return_value=mock_response)
    
    tool = SearchCompanyPolicyTool()
    result = await tool.execute(SearchCompanyPolicyInput(
        query="completely unrelated query xyz123",
        max_results=3
    ))

    assert result.success is True
    assert result.data is not None
    assert len(result.data["results"]) == 0


@pytest.mark.asyncio
async def test_search_company_policy_retrieval_error(mock_retrieval_service):
    """Test search when retrieval service returns error."""
    mock_response = MagicMock()
    mock_response.results = []
    mock_response.error = "RAG retrieval failed"
    
    mock_retrieval_service.search_company_policy = AsyncMock(return_value=mock_response)
    
    tool = SearchCompanyPolicyTool()
    result = await tool.execute(SearchCompanyPolicyInput(
        query="test query",
        max_results=3
    ))

    assert result.success is False
    assert result.error.error_code == "RETRIEVAL_ERROR"
    assert "RAG retrieval failed" in result.error.message