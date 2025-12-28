-- =====================================================
-- ADD PRODUCT-SPECIFIC FIELDS TO CATALOG ITEMS
-- =====================================================

-- Add dedicated product fields to catalog_items
ALTER TABLE catalog_items
    ADD COLUMN price NUMERIC(10, 2),  -- Price in dollars (e.g., 99.99)
    ADD COLUMN pricing_type TEXT CHECK (pricing_type IN ('one_time', 'monthly', 'yearly', 'usage_based')),
    ADD COLUMN product_url TEXT,  -- Link to vendor/product page
    ADD COLUMN vendor TEXT,  -- Vendor/manufacturer name
    ADD COLUMN sku TEXT;  -- Stock Keeping Unit or product code

-- Add same product fields to proposals (for ADD_ITEM and REPLACE_ITEM proposals)
ALTER TABLE proposals
    ADD COLUMN item_price NUMERIC(10, 2),
    ADD COLUMN item_pricing_type TEXT CHECK (item_pricing_type IN ('one_time', 'monthly', 'yearly', 'usage_based')),
    ADD COLUMN item_product_url TEXT,
    ADD COLUMN item_vendor TEXT,
    ADD COLUMN item_sku TEXT;

-- Create indexes on catalog_items for filtering
CREATE INDEX idx_catalog_items_vendor ON catalog_items(vendor);
CREATE INDEX idx_catalog_items_pricing_type ON catalog_items(pricing_type);
CREATE INDEX idx_catalog_items_sku ON catalog_items(sku);

-- Add comments explaining fields
COMMENT ON COLUMN catalog_items.metadata IS 'Additional flexible product attributes (brand, warranty, specifications, etc.)';
COMMENT ON COLUMN catalog_items.price IS 'Base price in USD. For usage-based pricing, this is the per-unit price.';
COMMENT ON COLUMN catalog_items.pricing_type IS 'Billing frequency: one_time (purchase), monthly (subscription), yearly (subscription), usage_based (metered)';
COMMENT ON COLUMN catalog_items.product_url IS 'URL to vendor product page or documentation';
COMMENT ON COLUMN catalog_items.vendor IS 'Vendor or manufacturer name (e.g., Dell, AWS, Logitech)';
COMMENT ON COLUMN catalog_items.sku IS 'Stock Keeping Unit, product code, or model number';

COMMENT ON COLUMN proposals.item_price IS 'Proposed item price (for ADD_ITEM and REPLACE_ITEM proposals)';
COMMENT ON COLUMN proposals.item_pricing_type IS 'Proposed pricing type (for ADD_ITEM and REPLACE_ITEM proposals)';
COMMENT ON COLUMN proposals.item_product_url IS 'Proposed product URL (for ADD_ITEM and REPLACE_ITEM proposals)';
COMMENT ON COLUMN proposals.item_vendor IS 'Proposed vendor name (for ADD_ITEM and REPLACE_ITEM proposals)';
COMMENT ON COLUMN proposals.item_sku IS 'Proposed SKU (for ADD_ITEM and REPLACE_ITEM proposals)';
