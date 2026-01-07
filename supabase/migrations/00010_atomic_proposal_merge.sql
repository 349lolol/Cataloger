-- Atomic functions for proposal merge operations
-- This ensures proposal status updates and catalog mutations are atomic,
-- preventing orphaned items or inconsistent state on failure.

-- Atomic function for ADD_ITEM proposal merge
CREATE OR REPLACE FUNCTION merge_add_item_proposal(
    p_proposal_id UUID,
    p_reviewed_by UUID,
    p_review_notes TEXT DEFAULT NULL,
    p_embedding vector(768) DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_proposal proposals%ROWTYPE;
    v_item_id UUID;
    v_result JSONB;
BEGIN
    -- Get and lock proposal
    SELECT * INTO v_proposal FROM proposals WHERE id = p_proposal_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Proposal not found: %', p_proposal_id;
    END IF;

    IF v_proposal.status != 'pending' THEN
        RAISE EXCEPTION 'Proposal is not pending';
    END IF;

    -- Create catalog item
    INSERT INTO catalog_items (
        org_id, name, description, category, created_by, status,
        price, pricing_type, product_url, vendor, sku, metadata
    ) VALUES (
        v_proposal.org_id, v_proposal.item_name, v_proposal.item_description,
        v_proposal.item_category, p_reviewed_by, 'active',
        v_proposal.item_price, v_proposal.item_pricing_type,
        v_proposal.item_product_url, v_proposal.item_vendor,
        v_proposal.item_sku, COALESCE(v_proposal.item_metadata, '{}')
    )
    RETURNING id INTO v_item_id;

    -- Create embedding if provided
    IF p_embedding IS NOT NULL THEN
        INSERT INTO catalog_item_embeddings (catalog_item_id, embedding)
        VALUES (v_item_id, p_embedding);
    END IF;

    -- Update proposal to merged
    UPDATE proposals SET
        status = 'merged',
        reviewed_by = p_reviewed_by,
        reviewed_at = now(),
        review_notes = p_review_notes,
        merged_at = now()
    WHERE id = p_proposal_id;

    -- Return result with created item ID
    SELECT jsonb_build_object(
        'proposal_id', p_proposal_id,
        'status', 'merged',
        'created_item_id', v_item_id
    ) INTO v_result;

    RETURN v_result;
END;
$$;

-- Atomic function for REPLACE_ITEM proposal merge
CREATE OR REPLACE FUNCTION merge_replace_item_proposal(
    p_proposal_id UUID,
    p_reviewed_by UUID,
    p_review_notes TEXT DEFAULT NULL,
    p_embedding vector(768) DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_proposal proposals%ROWTYPE;
    v_new_item_id UUID;
    v_result JSONB;
BEGIN
    -- Get and lock proposal
    SELECT * INTO v_proposal FROM proposals WHERE id = p_proposal_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Proposal not found: %', p_proposal_id;
    END IF;

    IF v_proposal.status != 'pending' THEN
        RAISE EXCEPTION 'Proposal is not pending';
    END IF;

    -- Create new catalog item
    INSERT INTO catalog_items (
        org_id, name, description, category, created_by, status,
        price, pricing_type, product_url, vendor, sku, metadata
    ) VALUES (
        v_proposal.org_id, v_proposal.item_name, v_proposal.item_description,
        v_proposal.item_category, p_reviewed_by, 'active',
        v_proposal.item_price, v_proposal.item_pricing_type,
        v_proposal.item_product_url, v_proposal.item_vendor,
        v_proposal.item_sku, COALESCE(v_proposal.item_metadata, '{}')
    )
    RETURNING id INTO v_new_item_id;

    -- Create embedding for new item if provided
    IF p_embedding IS NOT NULL THEN
        INSERT INTO catalog_item_embeddings (catalog_item_id, embedding)
        VALUES (v_new_item_id, p_embedding);
    END IF;

    -- Deprecate old item and link to replacement
    UPDATE catalog_items SET
        status = 'deprecated',
        replacement_item_id = v_new_item_id,
        updated_at = now()
    WHERE id = v_proposal.replacing_item_id;

    -- Update proposal to merged
    UPDATE proposals SET
        status = 'merged',
        reviewed_by = p_reviewed_by,
        reviewed_at = now(),
        review_notes = p_review_notes,
        merged_at = now()
    WHERE id = p_proposal_id;

    -- Return result with both item IDs
    SELECT jsonb_build_object(
        'proposal_id', p_proposal_id,
        'status', 'merged',
        'new_item_id', v_new_item_id,
        'old_item_id', v_proposal.replacing_item_id
    ) INTO v_result;

    RETURN v_result;
END;
$$;

-- Atomic function for DEPRECATE_ITEM proposal merge
CREATE OR REPLACE FUNCTION merge_deprecate_item_proposal(
    p_proposal_id UUID,
    p_reviewed_by UUID,
    p_review_notes TEXT DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_proposal proposals%ROWTYPE;
    v_result JSONB;
BEGIN
    -- Get and lock proposal
    SELECT * INTO v_proposal FROM proposals WHERE id = p_proposal_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Proposal not found: %', p_proposal_id;
    END IF;

    IF v_proposal.status != 'pending' THEN
        RAISE EXCEPTION 'Proposal is not pending';
    END IF;

    -- Deprecate the item
    UPDATE catalog_items SET
        status = 'deprecated',
        updated_at = now()
    WHERE id = v_proposal.replacing_item_id;

    -- Update proposal to merged
    UPDATE proposals SET
        status = 'merged',
        reviewed_by = p_reviewed_by,
        reviewed_at = now(),
        review_notes = p_review_notes,
        merged_at = now()
    WHERE id = p_proposal_id;

    -- Return result
    SELECT jsonb_build_object(
        'proposal_id', p_proposal_id,
        'status', 'merged',
        'deprecated_item_id', v_proposal.replacing_item_id
    ) INTO v_result;

    RETURN v_result;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION merge_add_item_proposal TO authenticated;
GRANT EXECUTE ON FUNCTION merge_add_item_proposal TO service_role;
GRANT EXECUTE ON FUNCTION merge_replace_item_proposal TO authenticated;
GRANT EXECUTE ON FUNCTION merge_replace_item_proposal TO service_role;
GRANT EXECUTE ON FUNCTION merge_deprecate_item_proposal TO authenticated;
GRANT EXECUTE ON FUNCTION merge_deprecate_item_proposal TO service_role;
