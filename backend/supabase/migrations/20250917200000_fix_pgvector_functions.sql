-- ResolveAI Fix match_document_chunks and insert_document_chunk functions
-- Part 18.1: Fix pgvector functions for 3072-dim embeddings

-- =============================================
-- DROP AND RECREATE match_document_chunks
-- =============================================

DROP FUNCTION IF EXISTS match_document_chunks(vector(3072), float, int, jsonb);

CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(3072),
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

GRANT EXECUTE ON FUNCTION match_document_chunks(vector(3072), float, int, jsonb) TO authenticated;
GRANT EXECUTE ON FUNCTION match_document_chunks(vector(3072), float, int, jsonb) TO service_role;

-- =============================================
-- DROP AND RECREATE insert_document_chunk
-- =============================================

DROP FUNCTION IF EXISTS insert_document_chunk(uuid, uuid, integer, text, vector, jsonb, timestamptz);

CREATE OR REPLACE FUNCTION insert_document_chunk(
    p_chunk_id uuid,
    p_document_id uuid,
    p_chunk_index integer,
    p_content text,
    p_embedding vector(3072),
    p_metadata jsonb DEFAULT '{}',
    p_created_at timestamptz DEFAULT now()
)
RETURNS SETOF document_chunks
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO document_chunks (
        id,
        document_id,
        chunk_index,
        content,
        embedding,
        metadata,
        created_at
    ) VALUES (
        p_chunk_id,
        p_document_id,
        p_chunk_index,
        p_content,
        p_embedding,
        p_metadata,
        p_created_at
    )
    ON CONFLICT (id) DO UPDATE SET
        document_id = EXCLUDED.document_id,
        chunk_index = EXCLUDED.chunk_index,
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding,
        metadata = EXCLUDED.metadata
    RETURNING *;
END;
$$;

GRANT EXECUTE ON FUNCTION insert_document_chunk(uuid, uuid, integer, text, vector, jsonb, timestamptz) TO authenticated;
GRANT EXECUTE ON FUNCTION insert_document_chunk(uuid, uuid, integer, text, vector, jsonb, timestamptz) TO service_role;