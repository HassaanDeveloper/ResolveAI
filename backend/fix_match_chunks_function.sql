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
    source character varying(255),
    version character varying(50)
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