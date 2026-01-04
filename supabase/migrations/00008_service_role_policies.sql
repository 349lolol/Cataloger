-- ============================================================================
-- MIGRATION 00008: Service Role Policies for All Tables
-- ============================================================================
-- Purpose: Allow backend services (using service role key) to access all data
-- The service role bypasses RLS by default, but these policies document intent
-- and ensure consistency across all tables.
-- ============================================================================

-- Service role can read all catalog items
CREATE POLICY "Service role can read all catalog items"
ON catalog_items FOR SELECT
TO service_role
USING (true);

-- Service role can read all embeddings
CREATE POLICY "Service role can read all embeddings"
ON catalog_item_embeddings FOR SELECT
TO service_role
USING (true);

-- Service role can read all requests
CREATE POLICY "Service role can read all requests"
ON requests FOR SELECT
TO service_role
USING (true);

-- Service role can read all proposals
CREATE POLICY "Service role can read all proposals"
ON proposals FOR SELECT
TO service_role
USING (true);

-- Service role can read all audit events
CREATE POLICY "Service role can read all audit events"
ON audit_events FOR SELECT
TO service_role
USING (true);

-- Service role can read all orgs
CREATE POLICY "Service role can read all orgs"
ON orgs FOR SELECT
TO service_role
USING (true);
