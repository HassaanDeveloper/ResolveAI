-- ResolveAI Synthetic Shipment Data
-- Part 04: Synthetic Northstar Commerce Data
-- Run this in Supabase SQL Editor AFTER seed_orders.sql

-- =============================================
-- SHIPMENTS
-- =============================================

-- Using subqueries to get order_id from order_number
-- Idempotent via (order_id, tracking_number) - but we don't have unique constraint on tracking_number per order
-- We'll use a CTE to avoid duplicates on re-run

WITH shipment_data AS (
    SELECT 
        o.id as order_id,
        s.carrier,
        s.tracking_number,
        s.status,
        s.estimated_delivery_date,
        s.delivered_at
    FROM (VALUES
        -- Order #10482: DELAYED - Key demo order (not arrived, estimated delivery passed)
        -- estimated_delivery_date is relative (now() - 10 days), NOT a fixed literal.
        -- calculate_refund.py treats a 'delayed' shipment as refund-eligible when
        -- days_delayed >= 7, so this must stay at 7 or more. 10 keeps it inside the
        -- eligible window on every future run instead of drifting to an absurd delay.
        ('10482', 'FedEx', 'FX123456789US', 'delayed', (now() - interval '10 days')::date, NULL),
        
        -- Order #10521: HIGH-VALUE - In transit
        ('10521', 'UPS', '1Z999AA10123456784', 'in_transit', '2025-09-10'::date, NULL),
        
        -- Order #10356: ALREADY REFUNDED - Was delivered
        ('10356', 'USPS', '9400100000000000000000', 'delivered', '2025-07-20'::date, '2025-07-19 14:30:00+00'::timestamptz),
        
        -- Order #10287: DELIVERED - Outside policy (delivered > 30 days ago)
        ('10287', 'FedEx', 'FX987654321US', 'delivered', '2025-06-15'::date, '2025-06-14 10:15:00+00'::timestamptz),
        
        -- Order #10612: SHIPPED - Cancellation should be escalated
        ('10612', 'UPS', '1Z999AA10123456785', 'in_transit', '2025-09-12'::date, NULL),
        
        -- Delivered orders
        ('10001', 'FedEx', 'FX111111111US', 'delivered', '2025-08-01'::date, '2025-07-31 09:00:00+00'::timestamptz),
        ('10002', 'UPS', '1Z999AA10123456701', 'delivered', '2025-08-02'::date, '2025-08-01 11:30:00+00'::timestamptz),
        ('10003', 'USPS', '9400100000000000000001', 'delivered', '2025-08-03'::date, '2025-08-02 14:00:00+00'::timestamptz),
        ('10004', 'FedEx', 'FX222222222US', 'delivered', '2025-08-04'::date, '2025-08-03 10:30:00+00'::timestamptz),
        ('10005', 'UPS', '1Z999AA10123456702', 'delivered', '2025-08-05'::date, '2025-08-04 13:45:00+00'::timestamptz),
        
        -- Processing orders (no shipment yet - pending)
        ('10101', 'FedEx', 'FX333333333US', 'pending', '2025-09-20'::date, NULL),
        ('10102', 'UPS', '1Z999AA10123456703', 'pending', '2025-09-21'::date, NULL),
        ('10103', 'USPS', '9400100000000000000002', 'pending', '2025-09-22'::date, NULL),
        ('10104', 'FedEx', 'FX444444444US', 'pending', '2025-09-23'::date, NULL),
        ('10105', 'UPS', '1Z999AA10123456704', 'pending', '2025-09-24'::date, NULL),
        
        -- Shipped orders (in transit)
        ('10201', 'FedEx', 'FX555555555US', 'in_transit', '2025-09-05'::date, NULL),
        ('10202', 'UPS', '1Z999AA10123456705', 'in_transit', '2025-09-06'::date, NULL),
        ('10203', 'USPS', '9400100000000000000003', 'in_transit', '2025-09-07'::date, NULL),
        ('10204', 'FedEx', 'FX666666666US', 'in_transit', '2025-09-08'::date, NULL),
        ('10205', 'UPS', '1Z999AA10123456706', 'in_transit', '2025-09-09'::date, NULL),
        
        -- More delivered orders
        ('10301', 'FedEx', 'FX777777777US', 'delivered', '2025-07-10'::date, '2025-07-09 15:00:00+00'::timestamptz),
        ('10302', 'UPS', '1Z999AA10123456707', 'delivered', '2025-07-11'::date, '2025-07-10 10:00:00+00'::timestamptz),
        ('10303', 'USPS', '9400100000000000000004', 'delivered', '2025-07-12'::date, '2025-07-11 12:00:00+00'::timestamptz),
        ('10304', 'FedEx', 'FX888888888US', 'delivered', '2025-07-13'::date, '2025-07-12 14:30:00+00'::timestamptz),
        ('10305', 'UPS', '1Z999AA10123456708', 'delivered', '2025-07-14'::date, '2025-07-13 11:00:00+00'::timestamptz),
        
        -- Cancelled orders (no shipment or failed)
        ('10401', 'FedEx', 'FX999999999US', 'failed', '2025-08-10'::date, NULL),
        ('10402', 'UPS', '1Z999AA10123456709', 'failed', '2025-08-11'::date, NULL),
        ('10403', 'USPS', '9400100000000000000005', 'failed', '2025-08-12'::date, NULL),
        ('10404', 'FedEx', 'FX000000000US', 'failed', '2025-08-13'::date, NULL),
        ('10405', 'UPS', '1Z999AA10123456710', 'failed', '2025-08-14'::date, NULL),
        
        -- Refunded orders (were delivered)
        ('10501', 'FedEx', 'FX121212121US', 'delivered', '2025-06-20'::date, '2025-06-19 13:00:00+00'::timestamptz),
        ('10502', 'UPS', '1Z999AA10123456711', 'delivered', '2025-06-21'::date, '2025-06-20 09:30:00+00'::timestamptz),
        ('10503', 'USPS', '9400100000000000000006', 'delivered', '2025-06-22'::date, '2025-06-21 14:00:00+00'::timestamptz),
        ('10504', 'FedEx', 'FX131313131US', 'delivered', '2025-06-23'::date, '2025-06-22 10:00:00+00'::timestamptz),
        ('10505', 'UPS', '1Z999AA10123456712', 'delivered', '2025-06-24'::date, '2025-06-23 16:00:00+00'::timestamptz),
        
        -- Pending order (no shipment created yet)
        -- ('10601', NULL, NULL, 'pending', NULL, NULL),  -- No shipment for pending order
        
        -- Failed shipment order
        ('10602', 'FedEx', 'FX141414141US', 'failed', '2025-08-25'::date, NULL)
    ) AS s(order_number, carrier, tracking_number, status, estimated_delivery_date, delivered_at)
    JOIN orders o ON o.order_number = s.order_number
)
INSERT INTO shipments (order_id, carrier, tracking_number, status, estimated_delivery_date, delivered_at)
SELECT order_id, carrier, tracking_number, status, estimated_delivery_date, delivered_at
FROM shipment_data
WHERE NOT EXISTS (
    SELECT 1 FROM shipments sh 
    WHERE sh.order_id = shipment_data.order_id 
    AND sh.tracking_number = shipment_data.tracking_number
);