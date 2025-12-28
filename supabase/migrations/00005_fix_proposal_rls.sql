-- =====================================================
-- FIX RLS POLICY FOR PROPOSAL CREATION
-- =====================================================
--
-- ISSUE: The original policy in 00002_rls_policies.sql allowed ANY
-- authenticated user to create proposals, violating the intended
-- role-based access control (only reviewers and admins should create proposals).
--
-- This migration fixes the defense-in-depth vulnerability by adding
-- proper role checking at the database level.

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "Users can create proposals" ON proposals;

-- Recreate with proper role-based restriction
-- Only users with 'reviewer' or 'admin' role can create proposals
CREATE POLICY "Reviewers can create proposals"
    ON proposals FOR INSERT
    WITH CHECK (
        org_id = public.user_org_id()
        AND proposed_by = auth.uid()
        AND public.has_role(ARRAY['reviewer', 'admin'])
    );
