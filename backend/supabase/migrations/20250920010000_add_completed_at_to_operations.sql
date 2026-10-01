-- Add completed_at column to operations table
-- Required by idempotency service for tracking operation completion time
-- Part of fix for PGRST204 error in mark_executed()

-- =============================================
-- ADD MISSING COLUMN TO OPERATIONS TABLE
-- =============================================

ALTER TABLE operations
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- =============================================
-- VERIFICATION
-- =============================================
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'operations' 
-- ORDER BY ordinal_position;