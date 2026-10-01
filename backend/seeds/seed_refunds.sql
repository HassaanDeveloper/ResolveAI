-- ResolveAI Synthetic Refund Data
-- Part 04: Synthetic Northstar Commerce Data
-- Run this in Supabase SQL Editor AFTER seed_shipments.sql

-- =============================================
-- REFUNDS
-- =============================================

-- Using subqueries to get order_id from order_number
-- operation_id is the idempotency key (unique)
-- Idempotent via operation_id unique constraint

INSERT INTO refunds (order_id, amount, currency, status, operation_id, processed_at) VALUES
    -- Order #10356: Already refunded (completed)
    (
        (SELECT id FROM orders WHERE order_number = '10356'),
        149.50, 'USD', 'completed',
        'refund-order-10356-149.50',
        '2025-07-25 10:00:00+00'::timestamptz
    ),
    -- Order #10501: Refunded
    (
        (SELECT id FROM orders WHERE order_number = '10501'),
        89.99, 'USD', 'completed',
        'refund-order-10501-89.99',
        '2025-07-01 14:30:00+00'::timestamptz
    ),
    -- Order #10502: Refunded
    (
        (SELECT id FROM orders WHERE order_number = '10502'),
        49.99, 'USD', 'completed',
        'refund-order-10502-49.99',
        '2025-07-02 11:15:00+00'::timestamptz
    ),
    -- Order #10503: Refunded (high value)
    (
        (SELECT id FROM orders WHERE order_number = '10503'),
        219.99, 'USD', 'completed',
        'refund-order-10503-219.99',
        '2025-07-03 09:45:00+00'::timestamptz
    ),
    -- Order #10504: Refunded
    (
        (SELECT id FROM orders WHERE order_number = '10504'),
        59.99, 'USD', 'completed',
        'refund-order-10504-59.99',
        '2025-07-04 16:20:00+00'::timestamptz
    ),
    -- Order #10505: Refunded
    (
        (SELECT id FROM orders WHERE order_number = '10505'),
        199.99, 'USD', 'completed',
        'refund-order-10505-199.99',
        '2025-07-05 13:10:00+00'::timestamptz
    ),
    -- Pending refunds (for demonstration of approval workflow)
    -- These are NOT completed yet - they represent potential refund requests
    (
        (SELECT id FROM orders WHERE order_number = '10482'),
        74.99, 'USD', 'pending',
        'refund-order-10482-74.99',
        NULL
    ),
    (
        (SELECT id FROM orders WHERE order_number = '10521'),
        299.99, 'USD', 'pending',
        'refund-order-10521-299.99',
        NULL
    ),
    (
        (SELECT id FROM orders WHERE order_number = '10612'),
        199.99, 'USD', 'pending',
        'refund-order-10612-199.99',
        NULL
    )
ON CONFLICT (operation_id) DO NOTHING;