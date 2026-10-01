-- Add policy_rule and risk_level columns to approval_requests table
-- These columns are required by the approval service

ALTER TABLE approval_requests 
ADD COLUMN policy_rule TEXT NULL,
ADD COLUMN risk_level VARCHAR(50) NULL DEFAULT 'MEDIUM';

-- Add comments for documentation
COMMENT ON COLUMN approval_requests.policy_rule IS 'The policy rule that triggered the approval requirement';
COMMENT ON COLUMN approval_requests.risk_level IS 'Risk level of the requested action (LOW, MEDIUM, HIGH)';