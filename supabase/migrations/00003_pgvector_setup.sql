-- =====================================================
-- PGVECTOR SETUP FOR SEMANTIC SEARCH
-- =====================================================

-- Create IVFFlat index for fast vector similarity search
-- Using cosine distance (recommended for sentence embeddings)
-- lists=100 is good for up to ~100k vectors per org
CREATE INDEX idx_catalog_item_embeddings_vector
    ON catalog_item_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- =====================================================
-- SEARCH RPC FUNCTION
-- =====================================================

-- Search catalog items by semantic similarity
-- This function enforces org-level isolation and returns top-K matches
CREATE OR REPLACE FUNCTION search_catalog_items(
    query_embedding vector(384),
    org_uuid UUID,
    similarity_threshold FLOAT DEFAULT 0.3,
    result_limit INT DEFAULT 10
)
RETURNS TABLE (
    item_id UUID,
    item_name TEXT,
    item_description TEXT,
    item_category TEXT,
    item_metadata JSONB,
    item_status TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.id AS item_id,
        ci.name AS item_name,
        ci.description AS item_description,
        ci.category AS item_category,
        ci.metadata AS item_metadata,
        ci.status AS item_status,
        1 - (cie.embedding <=> query_embedding) AS similarity_score
    FROM catalog_item_embeddings cie
    JOIN catalog_items ci ON ci.id = cie.catalog_item_id
    WHERE ci.org_id = org_uuid
        AND ci.status = 'active'
        AND 1 - (cie.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY cie.embedding <=> query_embedding ASC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION search_catalog_items TO authenticated;

-- =====================================================
-- HELPER FUNCTION: Get Item Embedding
-- =====================================================

-- Retrieve embedding for a specific catalog item
CREATE OR REPLACE FUNCTION get_item_embedding(item_uuid UUID)
RETURNS vector(384) AS $$
    SELECT embedding
    FROM catalog_item_embeddings
    WHERE catalog_item_id = item_uuid
    LIMIT 1;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_item_embedding TO authenticated;
