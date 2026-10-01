-- ResolveAI pgvector RPC Function for Similarity Search
-- Part 09: RAG Retrieval & Evidence Layer
-- Run this in Supabase SQL Editor AFTER 001_initial_schema.sql

-- =============================================
-- VECTOR SIMILARITY SEARCH RPC FUNCTION
-- =============================================

-- Function to find similar document chunks using cosine similarity
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.65,
    match_count int DEFAULT 10,
    filter_metadata jsonb DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_index integer,
    content text,
    metadata jsonb,
    similarity float,
    document_name text,
    source text,
    version text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.content,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity,
        d.name AS document_name,
        d.source,
        d.version
    FROM document_chunks dc
    JOIN documents d ON d.id = dc.document_id
    WHERE dc.embedding IS NOT NULL
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    AND (filter_metadata IS NULL OR dc.metadata @> filter_metadata)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =============================================
-- HNSW INDEX FOR FAST VECTOR SEARCH
-- =============================================

-- Create HNSW index on embeddings for fast similarity search
-- Run AFTER inserting document chunks for optimal performance
-- CREATE INDEX idx_document_chunks_embedding_hnsw 
-- ON document_chunks 
-- USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- =============================================
-- GRANT PERMISSIONS
-- =============================================

-- Grant execute permission to authenticated role (used by service role)
GRANT EXECUTE ON FUNCTION match_document_chunks(vector, float, int, jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION match_document_chunks(vector, float, int, jsonb) TO service_role;

-- =============================================
-- VERIFICATION QUERIES
-- =============================================

-- Test the function (run after ingesting documents):
-- SELECT * FROM match_document_chunks(
--     (SELECT embedding FROM document_chunks LIMIT 1),
--     0.5,
--     5,
--     NULL
-- );

-- Check index usage:
-- EXPLAIN ANALYZE SELECT * FROM match_document_chunks(
--     (SELECT embedding FROM document_chunks LIMIT 1),
--     0.5,
--     5,
--     NULL
-- );