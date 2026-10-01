import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag.retrieval.models import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    Evidence,
    SearchCompanyPolicyRequest,
    SearchCompanyPolicyResponse,
)
from app.rag.retrieval.service import RetrievalService


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    with patch("app.rag.retrieval.service.get_supabase_client") as mock_get:
        client = MagicMock()
        mock_get.return_value = client
        yield client


@pytest.fixture
def mock_embedding_service():
    with patch("app.rag.retrieval.service.gemini_embedding_service") as mock:
        yield mock


@pytest.fixture
def sample_evidence():
    return [
        Evidence(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="Refund Policy v2.1",
            section="Delayed Shipment Refunds",
            source="internal-policy",
            version="2.1",
            content="Customers are eligible for a full refund if a shipment is delayed...",
            relevance_score=0.92,
            metadata={"section_level": 2}
        ),
        Evidence(
            chunk_id="chunk-2",
            document_id="doc-2",
            document_name="Refund Approval Matrix",
            section="Approval Levels",
            source="internal-policy",
            version="1.0",
            content="Tier 1 (Auto): ≤$100, standard eligibility met...",
            relevance_score=0.85,
            metadata={"section_level": 2}
        ),
    ]


@pytest.mark.asyncio
async def test_retrieve_success(mock_supabase_client, mock_embedding_service, sample_evidence):
    """Test successful retrieval."""
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1] * 768)
    
    # Mock RPC response
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "Customers are eligible for a full refund if a shipment is delayed...",
            "metadata": {"section": "Delayed Shipment Refunds", "section_level": 2},
            "similarity": 0.92,
            "document_name": "Refund Policy v2.1",
            "source": "internal-policy",
            "version": "2.1"
        },
        {
            "id": "chunk-2",
            "document_id": "doc-2",
            "chunk_index": 1,
            "content": "Tier 1 (Auto): ≤$100, standard eligibility met...",
            "metadata": {"section": "Approval Levels", "section_level": 2},
            "similarity": 0.85,
            "document_name": "Refund Approval Matrix",
            "source": "internal-policy",
            "version": "1.0"
        }
    ]
    mock_supabase_client.rpc.return_value.execute.return_value = mock_rpc_result
    
    service = RetrievalService()
    request = RetrievalRequest(
        query="refund delayed shipment eligibility",
        max_results=5,
        similarity_threshold=0.65
    )
    
    response = await service.retrieve(request)
    
    assert isinstance(response, RetrievalResponse)
    assert response.query == "refund delayed shipment eligibility"
    assert len(response.evidence) == 2
    assert response.total_candidates == 2
    assert response.retrieval_strategy == RetrievalStrategy.SEMANTIC
    assert response.processing_time_ms >= 0
    
    # Check evidence structure
    ev1 = response.evidence[0]
    assert ev1.document_name == "Refund Policy v2.1"
    assert ev1.section == "Delayed Shipment Refunds"
    assert ev1.source == "internal-policy"
    assert ev1.version == "2.1"
    assert ev1.relevance_score == 0.92
    assert "delayed" in ev1.content.lower()


@pytest.mark.asyncio
async def test_retrieve_rpc_fallback(mock_supabase_client, mock_embedding_service):
    """Test fallback to raw query when RPC fails."""
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1] * 768)
    
    # RPC fails
    mock_supabase_client.rpc.return_value.execute.side_effect = Exception("RPC not found")
    
    # Raw query succeeds
    mock_table_result = MagicMock()
    mock_table_result.data = [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "Test content",
            "embedding": [0.1] * 768,
            "metadata": {"section": "Test Section"},
            "created_at": "2025-01-01T00:00:00+00:00",
            "documents": {"name": "Test Doc", "source": "internal-policy", "version": "1.0"}
        }
    ]
    mock_supabase_client.table.return_value.select.return_value.filter.return_value.limit.return_value.execute.return_value = mock_table_result
    
    service = RetrievalService()
    request = RetrievalRequest(query="test query", max_results=5)
    
    response = await service.retrieve(request)
    
    # Should still work with fallback
    assert isinstance(response, RetrievalResponse)


@pytest.mark.asyncio
async def test_retrieve_empty_results(mock_supabase_client, mock_embedding_service):
    """Test retrieval with no matching results."""
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1] * 768)
    mock_supabase_client.rpc.return_value.execute.return_value.data = []
    
    service = RetrievalService()
    request = RetrievalRequest(query="completely unrelated query xyz")
    
    response = await service.retrieve(request)
    
    assert response.evidence == []
    assert response.total_candidates == 0


@pytest.mark.asyncio
async def test_search_company_policy(mock_supabase_client, mock_embedding_service):
    """Test search_company_policy wrapper."""
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1] * 768)
    mock_supabase_client.rpc.return_value.execute.return_value.data = [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "Refund policy content...",
            "metadata": {"section": "Delayed Shipments"},
            "similarity": 0.90,
            "document_name": "Refund Policy v2.1",
            "source": "internal-policy",
            "version": "2.1"
        }
    ]
    
    service = RetrievalService()
    request = SearchCompanyPolicyRequest(query="delayed shipment refund", max_results=3)
    
    response = await service.search_company_policy(request)
    
    assert isinstance(response, SearchCompanyPolicyResponse)
    assert len(response.results) == 1
    assert response.error is None
    assert response.results[0].document_name == "Refund Policy v2.1"
    assert response.results[0].relevance_score == 0.90


@pytest.mark.asyncio
async def test_cosine_similarity():
    """Test cosine similarity calculation."""
    service = RetrievalService()
    
    # Identical vectors
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert service._cosine_similarity(a, b) == 1.0
    
    # Orthogonal vectors
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert service._cosine_similarity(a, b) == 0.0
    
    # Opposite vectors
    a = [1.0, 0.0, 0.0]
    b = [-1.0, 0.0, 0.0]
    assert service._cosine_similarity(a, b) == -1.0
    
    # Different lengths
    a = [1.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert service._cosine_similarity(a, b) == 0.0
    
    # Zero vectors
    a = [0.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert service._cosine_similarity(a, b) == 0.0


@pytest.mark.asyncio
async def test_rank_and_filter(mock_supabase_client, mock_embedding_service):
    """Test ranking and filtering of candidates."""
    mock_embedding_service.embed_query = AsyncMock(return_value=[0.1] * 768)
    
    # Return unsorted candidates
    mock_supabase_client.rpc.return_value.execute.return_value.data = [
        {"id": "1", "similarity": 0.70, "content": "Low relevance", "document_name": "Doc1", "source": "src", "version": "1.0", "metadata": {}, "document_id": "d1", "chunk_index": 0},
        {"id": "2", "similarity": 0.95, "content": "High relevance", "document_name": "Doc2", "source": "src", "version": "1.0", "metadata": {}, "document_id": "d2", "chunk_index": 0},
        {"id": "3", "similarity": 0.80, "content": "Medium relevance", "document_name": "Doc3", "source": "src", "version": "1.0", "metadata": {}, "document_id": "d3", "chunk_index": 0},
    ]
    
    service = RetrievalService()
    request = RetrievalRequest(query="test", max_results=2)
    
    response = await service.retrieve(request)
    
    # Should return top 2 by similarity
    assert len(response.evidence) == 2
    assert response.evidence[0].relevance_score == 0.95
    assert response.evidence[1].relevance_score == 0.80


@pytest.mark.asyncio
async def test_retrieval_error_handling(mock_supabase_client, mock_embedding_service):
    """Test error handling in retrieval."""
    mock_embedding_service.embed_query = AsyncMock(side_effect=Exception("API Error"))
    
    service = RetrievalService()
    request = RetrievalRequest(query="test query")
    
    response = await service.retrieve(request)
    
    # Should return empty evidence on error, not raise
    assert response.evidence == []
    assert response.total_candidates == 0


@pytest.mark.asyncio
async def test_search_company_policy_error(mock_supabase_client, mock_embedding_service):
    """Test search_company_policy error handling."""
    mock_embedding_service.embed_query = AsyncMock(side_effect=Exception("API Error"))
    
    service = RetrievalService()
    request = SearchCompanyPolicyRequest(query="test")
    
    response = await service.search_company_policy(request)
    
    assert response.results == []
    assert response.error is None  # Errors are logged, not returned to caller