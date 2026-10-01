-- ResolveAI Workflow State Columns Migration
-- Part 18: Add missing columns for workflow state persistence
-- Run this in Supabase SQL Editor AFTER 001_initial_schema.sql

-- =============================================
-- ADD MISSING COLUMNS TO RESOLUTIONS TABLE
-- =============================================

-- Workflow state persistence columns
ALTER TABLE resolutions 
ADD COLUMN IF NOT EXISTS retrieved_documents JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS tool_calls JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS policy_result JSONB,
ADD COLUMN IF NOT EXISTS approval JSONB,
ADD COLUMN IF NOT EXISTS action_result JSONB,
ADD COLUMN IF NOT EXISTS verification JSONB,
ADD COLUMN IF NOT EXISTS final_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS errors JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- =============================================
-- ADD MISSING COLUMNS TO DOCUMENTS TABLE
-- =============================================

-- Document ingestion status tracking
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS error TEXT,
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

-- =============================================
-- UPDATE EXISTING INDEXES
-- =============================================

-- No additional indexes needed for JSONB columns (GIN indexes can be added later if needed)

-- =============================================
-- VERIFICATION
-- =============================================
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'resolutions' ORDER BY ordinal_position;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position;