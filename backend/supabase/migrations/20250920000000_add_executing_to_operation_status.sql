-- Add "executing" to operation_status enum
-- This value is used by the idempotency service for in-progress operations
-- but was missing from the initial schema

ALTER TYPE operation_status ADD VALUE 'executing';