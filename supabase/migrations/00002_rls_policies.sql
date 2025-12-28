-- =====================================================
-- HELPER FUNCTIONS FOR RLS
-- =====================================================

-- Get current user's organization ID from their memberships
CREATE OR REPLACE FUNCTION public.user_org_id()
RETURNS UUID AS $$
    SELECT org_id
    FROM org_memberships
    WHERE user_id = auth.uid()
    LIMIT 1;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Get current user's role in a specific organization
CREATE OR REPLACE FUNCTION public.user_role(org_uuid UUID)
RETURNS TEXT AS $$
    SELECT role
    FROM org_memberships
    WHERE org_id = org_uuid AND user_id = auth.uid()
    LIMIT 1;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Check if user has at least one of the specified roles
CREATE OR REPLACE FUNCTION public.has_role(required_roles TEXT[])
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1
        FROM org_memberships
        WHERE user_id = auth.uid()
        AND role = ANY(required_roles)
    );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- =====================================================
-- ENABLE RLS ON ALL TABLES
-- =====================================================

ALTER TABLE orgs ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_item_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- ORGANIZATIONS POLICIES
-- =====================================================

-- Users can read their own organization
CREATE POLICY "Users can read own org"
    ON orgs FOR SELECT
    USING (id = public.user_org_id());

-- Only admins can create orgs (typically done via service role)
CREATE POLICY "Admins can create orgs"
    ON orgs FOR INSERT
    WITH CHECK (public.has_role(ARRAY['admin']));

-- Admins can update their own org
CREATE POLICY "Admins can update own org"
    ON orgs FOR UPDATE
    USING (id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- =====================================================
-- ORG MEMBERSHIPS POLICIES
-- =====================================================

-- Users can read memberships in their org
CREATE POLICY "Users can read own org memberships"
    ON org_memberships FOR SELECT
    USING (org_id = public.user_org_id());

-- Admins can create memberships in their org
CREATE POLICY "Admins can create memberships"
    ON org_memberships FOR INSERT
    WITH CHECK (org_id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- Admins can update memberships in their org
CREATE POLICY "Admins can update memberships"
    ON org_memberships FOR UPDATE
    USING (org_id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- Admins can delete memberships in their org
CREATE POLICY "Admins can delete memberships"
    ON org_memberships FOR DELETE
    USING (org_id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- =====================================================
-- CATALOG ITEMS POLICIES
-- =====================================================

-- All authenticated users can read items in their org
CREATE POLICY "Users can read org catalog items"
    ON catalog_items FOR SELECT
    USING (org_id = public.user_org_id());

-- Only admins can create catalog items directly
-- (normal users create via proposals)
CREATE POLICY "Admins can create catalog items"
    ON catalog_items FOR INSERT
    WITH CHECK (org_id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- Only admins can update catalog items
CREATE POLICY "Admins can update catalog items"
    ON catalog_items FOR UPDATE
    USING (org_id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- Only admins can delete catalog items
CREATE POLICY "Admins can delete catalog items"
    ON catalog_items FOR DELETE
    USING (org_id = public.user_org_id() AND public.has_role(ARRAY['admin']));

-- =====================================================
-- CATALOG ITEM EMBEDDINGS POLICIES
-- =====================================================

-- Users can read embeddings for items in their org
CREATE POLICY "Users can read embeddings"
    ON catalog_item_embeddings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM catalog_items
            WHERE catalog_items.id = catalog_item_embeddings.catalog_item_id
            AND catalog_items.org_id = public.user_org_id()
        )
    );

-- Service role manages embeddings (via backend)
-- Embedding inserts/updates happen via service role, so no user policies needed for INSERT/UPDATE

-- =====================================================
-- REQUESTS POLICIES
-- =====================================================

-- Users can read requests in their org
CREATE POLICY "Users can read org requests"
    ON requests FOR SELECT
    USING (org_id = public.user_org_id());

-- Any authenticated user can create requests in their org
CREATE POLICY "Users can create requests"
    ON requests FOR INSERT
    WITH CHECK (org_id = public.user_org_id() AND created_by = auth.uid());

-- Reviewers and admins can update requests (for approval/rejection)
CREATE POLICY "Reviewers can update requests"
    ON requests FOR UPDATE
    USING (org_id = public.user_org_id() AND public.has_role(ARRAY['reviewer', 'admin']));

-- =====================================================
-- PROPOSALS POLICIES
-- =====================================================

-- Users can read proposals in their org
CREATE POLICY "Users can read org proposals"
    ON proposals FOR SELECT
    USING (org_id = public.user_org_id());

-- Any authenticated user can create proposals in their org
CREATE POLICY "Users can create proposals"
    ON proposals FOR INSERT
    WITH CHECK (org_id = public.user_org_id() AND proposed_by = auth.uid());

-- Reviewers and admins can update proposals (for approval/rejection/merge)
CREATE POLICY "Reviewers can update proposals"
    ON proposals FOR UPDATE
    USING (org_id = public.user_org_id() AND public.has_role(ARRAY['reviewer', 'admin']));

-- =====================================================
-- AUDIT EVENTS POLICIES
-- =====================================================

-- Users can read audit events in their org
CREATE POLICY "Users can read org audit events"
    ON audit_events FOR SELECT
    USING (org_id = public.user_org_id());

-- Audit events are write-only via service role
-- No INSERT policy for users (handled by backend via service role)
