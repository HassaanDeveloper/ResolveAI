import time
import asyncio
from typing import List, Optional, Dict, Any
from app.rag.retrieval.models import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    Evidence,
    SearchCompanyPolicyRequest,
    SearchCompanyPolicyResponse,
)
from app.rag.embeddings import gemini_embedding_service
from app.services.database import get_supabase_client
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RetrievalService:
    """
    RAG retrieval service using pgvector similarity search.
    
    Pipeline:
    1. Query processing (normalization)
    2. Gemini embedding generation
    3. pgvector cosine similarity search
    4. Candidate filtering and ranking
    5. Evidence object construction
    """
    
    def __init__(self):
        self.supabase = None
        self._similarity_threshold_default = 0.65
    
    def _get_client(self):
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase
    
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Main retrieval entry point.
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate query embedding
            logger.info(f"Generating embedding for query: {request.query[:100]}")
            query_embedding = await gemini_embedding_service.embed_query(request.query)
            
            # Step 2: Perform vector similarity search
            logger.info(f"Searching vector store with threshold {request.similarity_threshold}")
            candidates = await self._vector_search(
                query_embedding=query_embedding,
                max_results=request.max_results * 2,  # Fetch more for filtering
                similarity_threshold=request.similarity_threshold,
                filter_metadata=request.filter_metadata
            )
            
            # Step 3: Rank and filter candidates
            evidence = self._rank_and_filter(
                candidates=candidates,
                max_results=request.max_results,
                query=request.query
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            response = RetrievalResponse(
                query=request.query,
                evidence=evidence,
                total_candidates=len(candidates),
                retrieval_strategy=request.strategy,
                processing_time_ms=processing_time
            )
            
            logger.info(f"Retrieved {len(evidence)} evidence items in {processing_time}ms")
            return response
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            return RetrievalResponse(
                query=request.query,
                evidence=[],
                total_candidates=0,
                retrieval_strategy=request.strategy,
                processing_time_ms=processing_time
            )
    
    async def _vector_search(
        self,
        query_embedding: List[float],
        max_results: int,
        similarity_threshold: float,
        filter_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Perform pgvector cosine similarity search.
        Uses the Supabase RPC function for vector search.
        """
        client = self._get_client()
        
        # Build filter conditions
        filter_conditions = {}
        for key, value in filter_metadata.items():
            if value is not None:
                filter_conditions[f"metadata->{key}"] = value
        
        # Try RPC function first (more efficient), fallback to raw query
        try:
            result = client.rpc(
                "match_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": max_results,
                    "filter_metadata": filter_conditions if filter_conditions else None
                }
            ).execute()
            
            if result.data:
                # RPC returns chunk_id, source_text, version_text
                return result.data
        except Exception as e:
            logger.warning(f"RPC function not available, falling back to raw query: {e}")
        
        # Fallback: Use raw Supabase query with vector similarity
        # This requires the pgvector extension and proper index
        try:
            # Construct raw query using PostgREST
            query = client.table("document_chunks").select(
                "id, document_id, chunk_index, content, embedding, metadata, created_at, documents!inner(name, source, version)"
            )
            
            # Apply metadata filters
            for key, value in filter_conditions.items():
                query = query.filter(key, "eq", value)
            
            result = query.limit(max_results).execute()
            
            # Compute cosine similarity in Python (fallback)
            candidates = []
            for row in result.data or []:
                if row.get("embedding"):
                    similarity = self._cosine_similarity(query_embedding, row["embedding"])
                    if similarity >= similarity_threshold:
                        candidates.append({
                            "id": row["id"],
                            "document_id": row["document_id"],
                            "chunk_index": row["chunk_index"],
                            "content": row["content"],
                            "metadata": row["metadata"],
                            "similarity": similarity,
                            "document_name": row.get("documents", {}).get("name", "Unknown"),
                            "source": row.get("documents", {}).get("source", "unknown"),
                            "version": row.get("documents", {}).get("version", "unknown")
                        })
            
            # Sort by similarity descending
            candidates.sort(key=lambda x: x["similarity"], reverse=True)
            return candidates[:max_results]
            
        except Exception as e:
            logger.error(f"Vector search fallback failed: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _rank_and_filter(
        self,
        candidates: List[Dict[str, Any]],
        max_results: int,
        query: str
    ) -> List[Evidence]:
        """
        Rank candidates and convert to Evidence objects.
        Currently just sorts by similarity, but can be extended with
        re-ranking, diversity, etc.
        """
        # Sort by similarity descending
        candidates.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        # Take top results
        top_candidates = candidates[:max_results]
        
        # Convert to Evidence objects
        evidence = []
        for candidate in top_candidates:
            ev = Evidence(
                chunk_id=candidate.get("chunk_id") or candidate.get("id"),
                document_id=candidate["document_id"],
                document_name=candidate.get("document_name", "Unknown"),
                section=candidate.get("metadata", {}).get("section", "Unknown"),
                source=candidate.get("source_text") or candidate.get("source", "unknown"),
                version=candidate.get("version_text") or candidate.get("version", "unknown"),
                content=candidate["content"],
                relevance_score=round(candidate.get("similarity", 0), 4),
                metadata=candidate.get("metadata", {})
            )
            evidence.append(ev)
        
        return evidence
    
    async def search_company_policy(self, request: SearchCompanyPolicyRequest) -> SearchCompanyPolicyResponse:
        """
        Search company policies using RAG retrieval.
        Replaces the temporary hardcoded search_company_policy tool.
        """
        retrieval_request = RetrievalRequest(
            query=request.query,
            max_results=request.max_results,
            similarity_threshold=0.65,
            strategy=RetrievalStrategy.SEMANTIC
        )
        
        response = await self.retrieve(retrieval_request)
        
        return SearchCompanyPolicyResponse(
            results=response.evidence,
            error=None
        )


# Singleton instance
retrieval_service = RetrievalService()