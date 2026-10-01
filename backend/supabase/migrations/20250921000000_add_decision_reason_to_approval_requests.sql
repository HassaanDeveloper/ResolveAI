-- Add decision_reason column to approval_requests table
-- This column is required by the approval service to store the human reviewer's decision reason

ALTER TABLE approval_requests 
ADD COLUMN decision_reason TEXT NULL;

-- Add comment for documentation
COMMENT ON COLUMN approval_requests.decision_reason IS 'Human reviewer''s reason for approving or rejecting the request';