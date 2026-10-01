import os
import asyncio
from typing import List, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiEmbeddingService:
    """Gemini API embedding service for gemini-embedding-001 (3072 dimensions)."""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-embedding-001"
        self.dimension = 3072
        self._client = None
    
    def _get_client(self):
        """Lazy initialize Gemini client."""
        if self._client is None:
            if not self.api_key or self.api_key == "your-gemini-api-key-here":
                raise ValueError("GEMINI_API_KEY not configured")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError:
                raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        return self._client
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        client = self._get_client()
        
        try:
            # Run in thread pool since Gemini SDK is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: client.embed_content(
                    model=f"models/{self.model}",
                    content=text,
                    task_type="retrieval_document"
                )
            )
            
            embedding = result['embedding']
            
            # Verify dimension
            if len(embedding) != self.dimension:
                logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                try:
                    emb = await self.embed_text(text)
                    batch_embeddings.append(emb)
                except Exception as e:
                    logger.error(f"Failed to embed text in batch: {e}")
                    # Use zero vector as fallback
                    batch_embeddings.append([0.0] * self.dimension)
            
            embeddings.extend(batch_embeddings)
            
            # Small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        client = self._get_client()
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: client.embed_content(
                    model=f"models/{self.model}",
                    content=query,
                    task_type="retrieval_query"
                )
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise


# Singleton instance
gemini_embedding_service = GeminiEmbeddingService()