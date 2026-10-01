import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from app.rag.models import Document, DocumentChunk, DocumentSource, DocumentStatus, IngestionResult
from app.rag.ingestion import IngestionService


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("app.rag.ingestion.get_supabase_client") as mock_get:
        client = MagicMock()
        mock_get.return_value = client
        yield client


@pytest.fixture
def sample_document():
    return Document(
        id="test-doc-id",
        name="Test Policy",
        source=DocumentSource.INTERNAL_POLICY,
        version="1.0",
        content="# Test Policy\n\nThis is a test policy content.",
        metadata={}
    )


@pytest.fixture
def sample_chunks(sample_document):
    return [
        DocumentChunk(
            document_id=sample_document.id,
            chunk_index=0,
            content="This is chunk 1 content",
            metadata={"section": "Section 1", "source": "internal-policy", "version": "1.0"}
        ),
        DocumentChunk(
            document_id=sample_document.id,
            chunk_index=1,
            content="This is chunk 2 content",
            metadata={"section": "Section 2", "source": "internal-policy", "version": "1.0"}
        ),
    ]


@pytest.mark.asyncio
async def test_ingest_document_success(mock_supabase, sample_document, sample_chunks):
    """Test successful document ingestion."""
    # Mock parser
    with patch("app.rag.ingestion.parse_and_chunk_document") as mock_parse:
        mock_parse.return_value = sample_chunks
        
        # Mock embedding service
        with patch("app.rag.ingestion.gemini_embedding_service") as mock_embedding:
            mock_embedding.embed_batch = AsyncMock(return_value=[[0.1]*768, [0.2]*768])
            
            # Mock Supabase responses
            mock_supabase.table.return_value.upsert.return_value.execute.return_value.data = [{"id": "doc-id"}]
            mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
            
            service = IngestionService()
            result = await service.ingest_document(sample_document)
            
            assert result.success is True
            assert result.document_id == sample_document.id
            assert result.chunks_created == 2
            assert result.embeddings_stored == 2
            assert result.processing_time_ms >= 0  # Can be 0 in fast tests


@pytest.mark.asyncio
async def test_ingest_document_no_chunks(mock_supabase, sample_document):
    """Test ingestion failure when no chunks created."""
    with patch("app.rag.ingestion.parse_and_chunk_document") as mock_parse:
        mock_parse.return_value = []
        
        service = IngestionService()
        result = await service.ingest_document(sample_document)
        
        assert result.success is False
        assert "No chunks created" in result.error


@pytest.mark.asyncio
async def test_ingest_document_embedding_failure(mock_supabase, sample_document, sample_chunks):
    """Test ingestion failure when embedding fails."""
    with patch("app.rag.ingestion.parse_and_chunk_document") as mock_parse:
        mock_parse.return_value = sample_chunks
        
        with patch("app.rag.ingestion.gemini_embedding_service") as mock_embedding:
            mock_embedding.embed_batch = AsyncMock(side_effect=Exception("API Error"))
            
            service = IngestionService()
            result = await service.ingest_document(sample_document)
            
            assert result.success is False
            assert "API Error" in result.error


@pytest.mark.asyncio
async def test_ingest_document_supabase_failure(mock_supabase, sample_document, sample_chunks):
    """Test ingestion failure when Supabase storage fails."""
    with patch("app.rag.ingestion.parse_and_chunk_document") as mock_parse:
        mock_parse.return_value = sample_chunks
        
        with patch("app.rag.ingestion.gemini_embedding_service") as mock_embedding:
            mock_embedding.embed_batch = AsyncMock(return_value=[[0.1]*768, [0.2]*768])
            
            # Mock Supabase to return empty data (failure)
            mock_supabase.table.return_value.upsert.return_value.execute.return_value.data = []
            
            service = IngestionService()
            result = await service.ingest_document(sample_document)
            
            assert result.success is False
            assert "Failed to store document" in result.error


@pytest.mark.asyncio
async def test_store_chunks_batching(mock_supabase, sample_document):
    """Test that chunks are stored in batches."""
    # Create 120 chunks (should create 3 batches of 50, 50, 20)
    chunks = [
        DocumentChunk(
            document_id=sample_document.id,
            chunk_index=i,
            content=f"Chunk {i} content",
            embedding=[0.1]*768,
            metadata={"section": f"Section {i}", "source": "internal-policy", "version": "1.0"}
        )
        for i in range(120)
    ]
    
    with patch("app.rag.ingestion.gemini_embedding_service") as mock_embedding:
        mock_embedding.embed_batch = AsyncMock(return_value=[[0.1]*768]*120)
        
        # Track batch calls
        upsert_calls = []
        def mock_upsert(data):
            upsert_calls.append(len(data))
            mock_result = MagicMock()
            mock_result.data = [{"id": f"chunk-{i}"} for i in range(len(data))]
            return mock_result
        
        mock_supabase.table.return_value.upsert.side_effect = mock_upsert
        
        service = IngestionService()
        await service._store_chunks(chunks)
        
        # Should have 3 batch calls: 50, 50, 20
        assert len(upsert_calls) == 3
        assert upsert_calls == [50, 50, 20]


@pytest.mark.asyncio
async def test_delete_document(mock_supabase):
    """Test document deletion."""
    mock_supabase.table.return_value.delete.return_value.execute.return_value.data = [{"id": "doc-id"}]
    
    service = IngestionService()
    result = await service.delete_document("test-doc-id")
    
    assert result is True
    # Verify both tables were called
    assert mock_supabase.table.call_count == 2


@pytest.mark.asyncio
async def test_get_ingestion_status(mock_supabase, sample_document):
    """Test getting ingestion status."""
    sample_document.created_at = datetime.utcnow()
    sample_document.updated_at = datetime.utcnow()
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": sample_document.id,
        "name": sample_document.name,
        "status": "completed"
    }
    
    # Mock chunk count
    mock_count_result = MagicMock()
    mock_count_result.count = 5
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_count_result
    
    service = IngestionService()
    status = await service.get_ingestion_status(sample_document.id)
    
    assert status is not None
    assert status["id"] == sample_document.id
    assert status["chunk_count"] == 5


@pytest.mark.asyncio
async def test_ingest_from_file_not_found():
    """Test ingestion from non-existent file."""
    service = IngestionService()
    result = await service.ingest_from_file(
        file_path="/nonexistent/path.md",
        document_name="Test",
        source="internal-policy",
        version="1.0"
    )
    
    assert result.success is False
    assert "Failed to read file" in result.error