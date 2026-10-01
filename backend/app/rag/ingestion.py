import asyncio
import time
from typing import List, Optional
from app.rag.models import Document, DocumentChunk, IngestionResult, DocumentStatus
from app.rag.parser import parse_and_chunk_document
from app.rag.embeddings import gemini_embedding_service
from app.services.database import get_supabase_client
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class IngestionService:
    """Orchestrates document ingestion: parse → chunk → embed → store."""
    
    def __init__(self):
        self.supabase = None
    
    def _get_client(self):
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase
    
    async def ingest_document(self, document: Document) -> IngestionResult:
        """
        Full ingestion pipeline for a single document.
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting ingestion for document: {document.name}")
            
            # Step 1: Update status to processing
            await self._update_document_status(document.id, DocumentStatus.PROCESSING)
            
            # Step 2: Parse and chunk
            logger.info(f"Parsing and chunking document: {document.name}")
            chunks = parse_and_chunk_document(document)
            logger.info(f"Created {len(chunks)} chunks")
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Step 3: Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await gemini_embedding_service.embed_batch(chunk_texts)
            
            # Attach embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # Step 4: Store in Supabase
            logger.info(f"Storing document and chunks in Supabase")
            await self._store_document(document)
            await self._store_chunks(chunks)
            
            # Step 5: Update status to completed
            await self._update_document_status(document.id, DocumentStatus.COMPLETED, processed_at=True)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            result = IngestionResult(
                success=True,
                document_id=document.id,
                chunks_created=len(chunks),
                embeddings_stored=len([c for c in chunks if c.embedding]),
                processing_time_ms=processing_time
            )
            
            logger.info(f"Ingestion completed for {document.name}: {result.chunks_created} chunks, {result.embeddings_stored} embeddings in {processing_time}ms")
            return result
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"Ingestion failed for {document.name}: {error_msg}")
            
            await self._update_document_status(document.id, DocumentStatus.FAILED, error=error_msg)
            
            return IngestionResult(
                success=False,
                document_id=document.id,
                error=error_msg,
                processing_time_ms=processing_time
            )
    
    async def _store_document(self, document: Document) -> None:
        """Store document metadata in Supabase."""
        client = self._get_client()
        
        data = {
            "id": document.id,
            "name": document.name,
            "source": document.source.value if hasattr(document.source, 'value') else str(document.source),
            "version": document.version,
            "content": document.content,
            "metadata": document.metadata,
            "created_at": document.created_at.isoformat() if document.created_at else None,
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = client.table("documents").upsert(data).execute()
        
        if not result.data:
            raise ValueError("Failed to store document")
    
    async def _store_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Store chunks with embeddings in Supabase using RPC for proper pgvector handling."""
        client = self._get_client()
        
        # Prepare chunk data for batch insert
        chunk_data = []
        for chunk in chunks:
            data = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata,
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
            }
            data = {k: v for k, v in data.items() if v is not None}
            chunk_data.append(data)
        
        # Insert in batches of 20 using RPC for proper pgvector handling
        batch_size = 20
        for i in range(0, len(chunk_data), batch_size):
            batch = chunk_data[i:i + batch_size]
            
            # Use RPC function for proper pgvector handling
            for chunk in batch:
                result = client.rpc("insert_document_chunk", {
                    "p_chunk_id": chunk["chunk_id"],
                    "p_document_id": chunk["document_id"],
                    "p_chunk_index": chunk["chunk_index"],
                    "p_content": chunk["content"],
                    "p_embedding": chunk["embedding"],
                    "p_metadata": chunk["metadata"],
                    "p_created_at": chunk["created_at"],
                }).execute()
                
                if not result.data:
                    raise ValueError(f"Failed to store chunk {chunk['chunk_id']}")
    
    async def _update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        processed_at: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Update document processing status."""
        client = self._get_client()
        
        update_data = {
            "status": status.value if hasattr(status, 'value') else str(status),
            "updated_at": "now()"
        }
        
        if processed_at:
            update_data["processed_at"] = "now()"
        if error:
            update_data["error"] = error
        
        client.table("documents").update(update_data).eq("id", document_id).execute()
    
    async def ingest_from_file(
        self,
        file_path: str,
        document_name: str,
        source: str,
        version: str,
        metadata: dict = None
    ) -> IngestionResult:
        """Convenience method to ingest from a file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return IngestionResult(
                success=False,
                error=f"Failed to read file: {e}"
            )
        
        from app.rag.models import DocumentSource
        
        document = Document(
            name=document_name,
            source=DocumentSource(source),
            version=version,
            content=content,
            metadata=metadata or {}
        )
        
        return await self.ingest_document(document)
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document and all its chunks."""
        client = self._get_client()
        
        # Delete chunks first (cascade should handle this, but explicit is safer)
        client.table("document_chunks").delete().eq("document_id", document_id).execute()
        
        # Delete document
        result = client.table("documents").delete().eq("id", document_id).execute()
        
        return bool(result.data)
    
    async def get_ingestion_status(self, document_id: str) -> Optional[dict]:
        """Get ingestion status for a document."""
        client = self._get_client()
        
        result = client.table("documents").select("*").eq("id", document_id).single().execute()
        
        if result.data:
            # Count chunks
            chunk_count = client.table("document_chunks").select("id", count="exact").eq("document_id", document_id).execute()
            result.data["chunk_count"] = chunk_count.count if chunk_count.count else 0
            return result.data
        
        return None


# Singleton instance
ingestion_service = IngestionService()