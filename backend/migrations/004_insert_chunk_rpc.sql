-- ResolveAI Insert Chunk RPC Function
-- Part 18.1: Add RPC function for proper pgvector chunk insertion
-- Run this in Supabase SQL Editor AFTER 001_initial_schema.sql and 002_rag_retrieval_rpc.sql

-- =============================================
-- INSERT DOCUMENT CHUNK RPC FUNCTION
-- =============================================

-- Function to insert a document chunk with proper pgvector handling
CREATE OR REPLACE FUNCTION insert_document_chunk(
    p_chunk_id uuid,
    p_document_id uuid,
    p_chunk_index integer,
    p_content text,
    p_embedding vector(3072),
    p_metadata jsonb DEFAULT '{}',
    p_created_at timestamptz DEFAULT now()
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_index integer,
    content text,
    embedding vector(3072),
    metadata jsonb,
    created_at timestamptz
)
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
    RETURNING
        id,
        document_id,
        chunk_index,
        content,
        embedding,
        metadata,
        created_at;
END;
$$;

-- Grant execute permission to authenticated role (used by service role)
GRANT EXECUTE ON FUNCTION insert_document_chunk(uuid, uuid, integer, text, vector, jsonb, timestamptz) TO authenticated;
GRANT EXECUTE ON FUNCTION insert_document_chunk(uuid, uuid, integer, text, vector, jsonb, timestamptz) TO service_role;

-- =============================================
-- VERIFICATION
-- =============================================
-- Test the function:
-- SELECT * FROM insert_document_chunk(
--     gen_random_uuid(),
--     (SELECT id FROM documents LIMIT 1),
--     0,
--     'test content',
--     ARRAY[0.1]::vector(3072),
--     '{}'::jsonb,
--     now()
-- );