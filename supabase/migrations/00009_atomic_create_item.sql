-- Atomic function to create catalog item with embedding
-- This ensures both item and embedding are inserted in a single transaction,
-- preventing orphaned items if embedding insertion fails.

CREATE OR REPLACE FUNCTION create_catalog_item_with_embedding(
    p_org_id UUID,
    p_name TEXT,
    p_description TEXT,
    p_category TEXT,
    p_created_by UUID,
    p_status TEXT DEFAULT 'active',
    p_price NUMERIC(10,2) DEFAULT NULL,
    p_pricing_type TEXT DEFAULT NULL,
    p_product_url TEXT DEFAULT NULL,
    p_vendor TEXT DEFAULT NULL,
    p_sku TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}',
    p_embedding vector(768) DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER  -- Runs with owner privileges (bypasses RLS for embedding insert)
AS $$
DECLARE
    v_item_id UUID;
    v_item JSONB;
BEGIN
    -- Insert catalog item
    INSERT INTO catalog_items (
        org_id, name, description, category, created_by, status,
        price, pricing_type, product_url, vendor, sku, metadata
    ) VALUES (
        p_org_id, p_name, p_description, p_category, p_created_by, p_status,
        p_price, p_pricing_type, p_product_url, p_vendor, p_sku, p_metadata
    )
    RETURNING id INTO v_item_id;

    -- Insert embedding if provided
    IF p_embedding IS NOT NULL THEN
        INSERT INTO catalog_item_embeddings (catalog_item_id, embedding)
        VALUES (v_item_id, p_embedding);
    END IF;

    -- Return the created item as JSON
    SELECT jsonb_build_object(
        'id', id,
        'org_id', org_id,
        'name', name,
        'description', description,
        'category', category,
        'status', status,
        'created_by', created_by,
        'created_at', created_at,
        'updated_at', updated_at,
        'price', price,
        'pricing_type', pricing_type,
        'product_url', product_url,
        'vendor', vendor,
        'sku', sku,
        'metadata', metadata
    ) INTO v_item
    FROM catalog_items WHERE id = v_item_id;

    RETURN v_item;
END;
$$;

-- Grant execute to authenticated users and service role
GRANT EXECUTE ON FUNCTION create_catalog_item_with_embedding TO authenticated;
GRANT EXECUTE ON FUNCTION create_catalog_item_with_embedding TO service_role;
