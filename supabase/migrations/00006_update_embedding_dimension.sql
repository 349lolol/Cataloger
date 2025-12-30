-- =====================================================
-- UPDATE EMBEDDING DIMENSION FROM 384 TO 768
-- =====================================================
-- This migration updates the vector dimension to match
-- Gemini text-embedding-004 (768 dimensions)
-- Previous: sentence-transformers/all-MiniLM-L6-v2 (384)
-- =====================================================

-- Step 1: Drop dependent objects
DROP INDEX IF EXISTS idx_catalog_item_embeddings_vector;
DROP FUNCTION IF EXISTS search_catalog_items(vector, UUID, FLOAT, INT);
DROP FUNCTION IF EXISTS get_item_embedding(UUID);

-- Step 2: Update the embedding column
ALTER TABLE catalog_item_embeddings
    DROP COLUMN embedding;

ALTER TABLE catalog_item_embeddings
    ADD COLUMN embedding vector(768);

ALTER TABLE catalog_item_embeddings
    ALTER COLUMN model_version SET DEFAULT 'models/text-embedding-004';

-- Step 3: Recreate the IVFFlat index
CREATE INDEX idx_catalog_item_embeddings_vector
    ON catalog_item_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Step 4: Recreate search function with new dimension
CREATE OR REPLACE FUNCTION search_catalog_items(
    query_embedding vector(768),
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

GRANT EXECUTE ON FUNCTION search_catalog_items TO authenticated;

-- Step 5: Recreate helper function
CREATE OR REPLACE FUNCTION get_item_embedding(item_uuid UUID)
RETURNS vector(768) AS $$
    SELECT embedding
    FROM catalog_item_embeddings
    WHERE catalog_item_id = item_uuid
    LIMIT 1;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_item_embedding TO authenticated;
