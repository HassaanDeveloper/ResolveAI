-- Minimal targeted seed correction for order 10482 only.
-- Mirrors the change made in seeds/seed_shipments.sql:
--   estimated_delivery_date: '2025-08-15'  ->  (now() - interval '10 days')
-- 10 days keeps days_delayed >= 7, the threshold in calculate_refund.py
-- that marks a 'delayed' shipment refund-eligible.
UPDATE shipments
SET estimated_delivery_date = (now() - interval '10 days')::date
WHERE order_id = (SELECT id FROM orders WHERE order_number = '10482')
  AND tracking_number = 'FX123456789US';

-- The stale completed refund from earlier demo runs is what drove eligible_amount
-- to 0.00 (74.99 total - 74.99 already refunded). Clear it so the low-value
-- scenario is reproducible.
DELETE FROM refunds
WHERE order_id = (SELECT id FROM orders WHERE order_number = '10482');

-- Clear the idempotency ledger entry for the same operation_id.
DELETE FROM operations
WHERE operation_id = 'refund-order-10482-74.99';

-- Drop prior resolution rows for this order so the console starts clean.
-- approval_requests first, since it references resolutions(id).
DELETE FROM approval_requests
WHERE resolution_id IN (SELECT id FROM resolutions WHERE order_number = '10482');
DELETE FROM resolutions WHERE order_number = '10482';
