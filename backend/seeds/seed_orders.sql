-- ResolveAI Synthetic Order Data
-- Part 04: Synthetic Northstar Commerce Data
-- Run this in Supabase SQL Editor AFTER seed_customers.sql

-- =============================================
-- ORDERS (40 synthetic orders)
-- =============================================

-- Using subqueries to get customer_id from external_customer_id
-- Idempotent via order_number unique constraint

INSERT INTO orders (order_number, customer_id, status, total_amount, currency) VALUES
    -- Order #10482: DELAYED/NOT ARRIVED - Low-risk refund ($74.99) - KEY DEMO ORDER
    ('10482', (SELECT id FROM customers WHERE external_customer_id = 'CUST-001'), 'shipped', 74.99, 'USD'),

    -- Order #10521: HIGH-VALUE - Requires approval for refund ($299.99)
    ('10521', (SELECT id FROM customers WHERE external_customer_id = 'CUST-002'), 'shipped', 299.99, 'USD'),

    -- Order #10356: ALREADY REFUNDED
    ('10356', (SELECT id FROM customers WHERE external_customer_id = 'CUST-003'), 'refunded', 149.50, 'USD'),

    -- Order #10287: DELIVERED - Outside policy conditions (delivered > 30 days ago)
    ('10287', (SELECT id FROM customers WHERE external_customer_id = 'CUST-004'), 'delivered', 89.99, 'USD'),

    -- Order #10612: SHIPPED - Cancellation should be escalated
    ('10612', (SELECT id FROM customers WHERE external_customer_id = 'CUST-005'), 'shipped', 199.99, 'USD'),

    -- Additional orders for variety
    ('10001', (SELECT id FROM customers WHERE external_customer_id = 'CUST-006'), 'delivered', 129.99, 'USD'),
    ('10002', (SELECT id FROM customers WHERE external_customer_id = 'CUST-007'), 'delivered', 59.99, 'USD'),
    ('10003', (SELECT id FROM customers WHERE external_customer_id = 'CUST-008'), 'delivered', 219.99, 'USD'),
    ('10004', (SELECT id FROM customers WHERE external_customer_id = 'CUST-009'), 'delivered', 79.99, 'USD'),
    ('10005', (SELECT id FROM customers WHERE external_customer_id = 'CUST-010'), 'delivered', 349.99, 'USD'),

    ('10101', (SELECT id FROM customers WHERE external_customer_id = 'CUST-011'), 'processing', 189.99, 'USD'),
    ('10102', (SELECT id FROM customers WHERE external_customer_id = 'CUST-012'), 'processing', 99.99, 'USD'),
    ('10103', (SELECT id FROM customers WHERE external_customer_id = 'CUST-013'), 'processing', 259.99, 'USD'),
    ('10104', (SELECT id FROM customers WHERE external_customer_id = 'CUST-014'), 'processing', 49.99, 'USD'),
    ('10105', (SELECT id FROM customers WHERE external_customer_id = 'CUST-015'), 'processing', 159.99, 'USD'),

    ('10201', (SELECT id FROM customers WHERE external_customer_id = 'CUST-016'), 'shipped', 79.99, 'USD'),
    ('10202', (SELECT id FROM customers WHERE external_customer_id = 'CUST-017'), 'shipped', 199.99, 'USD'),
    ('10203', (SELECT id FROM customers WHERE external_customer_id = 'CUST-018'), 'shipped', 129.99, 'USD'),
    ('10204', (SELECT id FROM customers WHERE external_customer_id = 'CUST-019'), 'shipped', 89.99, 'USD'),
    ('10205', (SELECT id FROM customers WHERE external_customer_id = 'CUST-020'), 'shipped', 229.99, 'USD'),

    ('10301', (SELECT id FROM customers WHERE external_customer_id = 'CUST-021'), 'delivered', 69.99, 'USD'),
    ('10302', (SELECT id FROM customers WHERE external_customer_id = 'CUST-022'), 'delivered', 179.99, 'USD'),
    ('10303', (SELECT id FROM customers WHERE external_customer_id = 'CUST-023'), 'delivered', 99.99, 'USD'),
    ('10304', (SELECT id FROM customers WHERE external_customer_id = 'CUST-024'), 'delivered', 149.99, 'USD'),
    ('10305', (SELECT id FROM customers WHERE external_customer_id = 'CUST-025'), 'delivered', 89.99, 'USD'),

    ('10401', (SELECT id FROM customers WHERE external_customer_id = 'CUST-001'), 'cancelled', 119.99, 'USD'),
    ('10402', (SELECT id FROM customers WHERE external_customer_id = 'CUST-002'), 'cancelled', 69.99, 'USD'),
    ('10403', (SELECT id FROM customers WHERE external_customer_id = 'CUST-003'), 'cancelled', 199.99, 'USD'),
    ('10404', (SELECT id FROM customers WHERE external_customer_id = 'CUST-004'), 'cancelled', 139.99, 'USD'),
    ('10405', (SELECT id FROM customers WHERE external_customer_id = 'CUST-005'), 'cancelled', 99.99, 'USD'),

    ('10501', (SELECT id FROM customers WHERE external_customer_id = 'CUST-006'), 'refunded', 89.99, 'USD'),
    ('10502', (SELECT id FROM customers WHERE external_customer_id = 'CUST-007'), 'refunded', 49.99, 'USD'),
    ('10503', (SELECT id FROM customers WHERE external_customer_id = 'CUST-008'), 'refunded', 219.99, 'USD'),
    ('10504', (SELECT id FROM customers WHERE external_customer_id = 'CUST-009'), 'refunded', 59.99, 'USD'),
    ('10505', (SELECT id FROM customers WHERE external_customer_id = 'CUST-010'), 'refunded', 199.99, 'USD'),

    -- Edge case: pending order
    ('10601', (SELECT id FROM customers WHERE external_customer_id = 'CUST-011'), 'pending', 149.99, 'USD'),
    -- Edge case: failed shipment
    ('10602', (SELECT id FROM customers WHERE external_customer_id = 'CUST-012'), 'shipped', 99.99, 'USD')
ON CONFLICT (order_number) DO NOTHING;