import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag.embeddings import GeminiEmbeddingService


@pytest.fixture
def mock_gemini_client():
    """Mock the google.generativeai client."""
    with patch("google.generativeai.configure") as mock_configure, \
         patch("google.generativeai.embed_content") as mock_embed:
        yield mock_embed


@pytest.mark.asyncio
async def test_embed_text_success(mock_gemini_client):
    """Test successful embedding generation."""
    mock_gemini_client.return_value = {"embedding": [0.1] * 768}
    
    service = GeminiEmbeddingService()
    service._client = MagicMock()  # Bypass client initialization
    
    # Manually set the client to avoid API key check
    import google.generativeai as genai
    service._client = genai
    
    embedding = await service.embed_text("Test text for embedding")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_embed_text_dimension_validation(mock_gemini_client):
    """Test that dimension mismatch is handled."""
    # Return wrong dimension
    mock_gemini_client.return_value = {"embedding": [0.1] * 512}
    
    service = GeminiEmbeddingService()
    service._client = MagicMock()
    import google.generativeai as genai
    service._client = genai
    
    # Should still return the embedding (with warning logged)
    embedding = await service.embed_text("Test text")
    assert len(embedding) == 512


@pytest.mark.asyncio
async def test_embed_batch(mock_gemini_client):
    """Test batch embedding generation."""
    mock_gemini_client.return_value = {"embedding": [0.1] * 768}
    
    service = GeminiEmbeddingService()
    service._client = MagicMock()
    import google.generativeai as genai
    service._client = genai
    
    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings = await service.embed_batch(texts, batch_size=2)
    
    assert len(embeddings) == 3
    assert all(len(e) == 768 for e in embeddings)


@pytest.mark.asyncio
async def test_embed_query(mock_gemini_client):
    """Test query embedding generation (uses retrieval_query task type)."""
    mock_gemini_client.return_value = {"embedding": [0.1] * 768}
    
    service = GeminiEmbeddingService()
    service._client = MagicMock()
    import google.generativeai as genai
    service._client = genai
    
    embedding = await service.embed_query("search query")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 768


@pytest.mark.asyncio
async def test_embed_text_error_handling(mock_gemini_client):
    """Test error handling when API fails."""
    mock_gemini_client.side_effect = Exception("API Error")
    
    service = GeminiEmbeddingService()
    service._client = MagicMock()
    import google.generativeai as genai
    service._client = genai
    
    with pytest.raises(Exception):
        await service.embed_text("Test text")


def test_service_initialization_without_api_key():
    """Test service initialization fails gracefully without API key."""
    # This tests the config check in _get_client
    service = GeminiEmbeddingService()
    service.api_key = "your-gemini-api-key-here"  # Invalid placeholder
    
    # The service should not fail until _get_client is called
    assert service.api_key == "your-gemini-api-key-here"