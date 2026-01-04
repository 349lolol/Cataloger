-- ============================================================================
-- MIGRATION 00007: Service Role Policy for org_memberships
-- ============================================================================
-- Purpose: Allow backend auth middleware to look up any user's org membership
-- The service role client bypasses RLS by default, but this policy documents
-- the intent and ensures consistency.
-- ============================================================================

-- Service role can read all memberships (for backend auth middleware)
CREATE POLICY "Service role can read all memberships"
ON org_memberships FOR SELECT
TO service_role
USING (true);
