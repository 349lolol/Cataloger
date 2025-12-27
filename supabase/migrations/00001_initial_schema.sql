-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Organizations (Tenant Root)
CREATE TABLE orgs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Organization Memberships (User → Org Mapping with Roles)
CREATE TABLE org_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- Supabase auth.users.id
    role TEXT NOT NULL CHECK (role IN ('requester', 'reviewer', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

-- Catalog Items (Products/Services)
CREATE TABLE catalog_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    metadata JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated')),
    replacement_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL,
    created_by UUID NOT NULL, -- User who created this item
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Catalog Item Embeddings (Vector Storage)
CREATE TABLE catalog_item_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_item_id UUID NOT NULL REFERENCES catalog_items(id) ON DELETE CASCADE,
    embedding vector(384), -- all-MiniLM-L6-v2 dimension
    model_version TEXT NOT NULL DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(catalog_item_id)
);

-- Requests (Search → Request Flow)
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    created_by UUID NOT NULL, -- User who created request
    search_query TEXT NOT NULL,
    search_results JSONB, -- Store search results snapshot
    justification TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID, -- User who reviewed
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Proposals (Governance for Catalog Changes)
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    proposal_type TEXT NOT NULL CHECK (proposal_type IN ('ADD_ITEM', 'REPLACE_ITEM', 'DEPRECATE_ITEM')),
    proposed_by UUID NOT NULL, -- User who proposed
    request_id UUID REFERENCES requests(id) ON DELETE SET NULL, -- Optional link to request

    -- Item details (for ADD/REPLACE)
    item_name TEXT,
    item_description TEXT,
    item_category TEXT,
    item_metadata JSONB DEFAULT '{}',

    -- For REPLACE/DEPRECATE operations
    replacing_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL,

    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'merged')),
    reviewed_by UUID,
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit Events (Immutable Event Log)
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- e.g., 'catalog.item.created', 'proposal.approved'
    actor_id UUID NOT NULL, -- User who performed action
    resource_type TEXT NOT NULL, -- e.g., 'catalog_item', 'proposal'
    resource_id UUID NOT NULL, -- ID of affected resource
    metadata JSONB DEFAULT '{}', -- Additional event data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Organization memberships
CREATE INDEX idx_org_memberships_org_id ON org_memberships(org_id);
CREATE INDEX idx_org_memberships_user_id ON org_memberships(user_id);

-- Catalog items
CREATE INDEX idx_catalog_items_org_id ON catalog_items(org_id);
CREATE INDEX idx_catalog_items_status ON catalog_items(status);
CREATE INDEX idx_catalog_items_category ON catalog_items(category);
CREATE INDEX idx_catalog_items_created_at ON catalog_items(created_at DESC);

-- Requests
CREATE INDEX idx_requests_org_id ON requests(org_id);
CREATE INDEX idx_requests_created_by ON requests(created_by);
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_created_at ON requests(created_at DESC);

-- Proposals
CREATE INDEX idx_proposals_org_id ON proposals(org_id);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_request_id ON proposals(request_id);
CREATE INDEX idx_proposals_created_at ON proposals(created_at DESC);

-- Audit events
CREATE INDEX idx_audit_events_org_id ON audit_events(org_id);
CREATE INDEX idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at DESC);
