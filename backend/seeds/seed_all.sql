-- ResolveAI Master Seed Script
-- Part 04: Synthetic Northstar Commerce Data
-- Run this single file in Supabase SQL Editor to seed all data
-- This file includes all seed data in the correct order

-- =============================================
-- EXTENSIONS (ensure they exist)
-- =============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- SEED CUSTOMERS (25)
-- =============================================
INSERT INTO customers (external_customer_id, name, email, account_status) VALUES
    ('CUST-001', 'Sarah Mitchell', 'sarah.mitchell@email.com', 'active'),
    ('CUST-002', 'James Chen', 'james.chen@email.com', 'active'),
    ('CUST-003', 'Maria Rodriguez', 'maria.rodriguez@email.com', 'active'),
    ('CUST-004', 'David Thompson', 'david.thompson@email.com', 'active'),
    ('CUST-005', 'Jennifer Park', 'jennifer.park@email.com', 'active'),
    ('CUST-006', 'Robert Kim', 'robert.kim@email.com', 'active'),
    ('CUST-007', 'Lisa Anderson', 'lisa.anderson@email.com', 'active'),
    ('CUST-008', 'Michael Brown', 'michael.brown@email.com', 'suspended'),
    ('CUST-009', 'Amanda Wilson', 'amanda.wilson@email.com', 'active'),
    ('CUST-010', 'Christopher Lee', 'christopher.lee@email.com', 'active'),
    ('CUST-011', 'Jessica Martinez', 'jessica.martinez@email.com', 'active'),
    ('CUST-012', 'Daniel Garcia', 'daniel.garcia@email.com', 'active'),
    ('CUST-013', 'Ashley Taylor', 'ashley.taylor@email.com', 'active'),
    ('CUST-014', 'Matthew White', 'matthew.white@email.com', 'active'),
    ('CUST-015', 'Stephanie Harris', 'stephanie.harris@email.com', 'closed'),
    ('CUST-016', 'Andrew Clark', 'andrew.clark@email.com', 'active'),
    ('CUST-017', 'Nicole Lewis', 'nicole.lewis@email.com', 'active'),
    ('CUST-018', 'Joshua Walker', 'joshua.walker@email.com', 'active'),
    ('CUST-019', 'Emily Hall', 'emily.hall@email.com', 'active'),
    ('CUST-020', 'Ryan Allen', 'ryan.allen@email.com', 'active'),
    ('CUST-021', 'Megan Young', 'megan.young@email.com', 'active'),
    ('CUST-022', 'Brandon King', 'brandon.king@email.com', 'active'),
    ('CUST-023', 'Rachel Scott', 'rachel.scott@email.com', 'active'),
    ('CUST-024', 'Tyler Adams', 'tyler.adams@email.com', 'active'),
    ('CUST-025', 'Lauren Baker', 'lauren.baker@email.com', 'active')
ON CONFLICT (external_customer_id) DO NOTHING;

-- =============================================
-- SEED ORDERS (40)
-- =============================================
INSERT INTO orders (order_number, customer_id, status, total_amount, currency) VALUES
    -- Key demonstration orders
    ('10482', (SELECT id FROM customers WHERE external_customer_id = 'CUST-001'), 'shipped', 74.99, 'USD'),
    ('10521', (SELECT id FROM customers WHERE external_customer_id = 'CUST-002'), 'shipped', 299.99, 'USD'),
    ('10356', (SELECT id FROM customers WHERE external_customer_id = 'CUST-003'), 'refunded', 149.50, 'USD'),
    ('10287', (SELECT id FROM customers WHERE external_customer_id = 'CUST-004'), 'delivered', 89.99, 'USD'),
    ('10612', (SELECT id FROM customers WHERE external_customer_id = 'CUST-005'), 'shipped', 199.99, 'USD'),
    
    -- Additional orders
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

    ('10601', (SELECT id FROM customers WHERE external_customer_id = 'CUST-011'), 'pending', 149.99, 'USD'),
    ('10602', (SELECT id FROM customers WHERE external_customer_id = 'CUST-012'), 'shipped', 99.99, 'USD')
ON CONFLICT (order_number) DO NOTHING;

-- =============================================
-- SEED SHIPMENTS
-- =============================================
WITH shipment_data AS (
    SELECT 
        o.id as order_id,
        s.carrier,
        s.tracking_number,
        s.status,
        s.estimated_delivery_date,
        s.delivered_at
    FROM (VALUES
        -- Key demo orders
        ('10482', 'FedEx', 'FX123456789US', 'delayed', '2025-08-15'::date, NULL),
        ('10521', 'UPS', '1Z999AA10123456784', 'in_transit', '2025-09-10'::date, NULL),
        ('10356', 'USPS', '9400100000000000000000', 'delivered', '2025-07-20'::date, '2025-07-19 14:30:00+00'::timestamptz),
        ('10287', 'FedEx', 'FX987654321US', 'delivered', '2025-06-15'::date, '2025-06-14 10:15:00+00'::timestamptz),
        ('10612', 'UPS', '1Z999AA10123456785', 'in_transit', '2025-09-12'::date, NULL),
        
        -- Delivered orders
        ('10001', 'FedEx', 'FX111111111US', 'delivered', '2025-08-01'::date, '2025-07-31 09:00:00+00'::timestamptz),
        ('10002', 'UPS', '1Z999AA10123456701', 'delivered', '2025-08-02'::date, '2025-08-01 11:30:00+00'::timestamptz),
        ('10003', 'USPS', '9400100000000000000001', 'delivered', '2025-08-03'::date, '2025-08-02 14:00:00+00'::timestamptz),
        ('10004', 'FedEx', 'FX222222222US', 'delivered', '2025-08-04'::date, '2025-08-03 10:30:00+00'::timestamptz),
        ('10005', 'UPS', '1Z999AA10123456702', 'delivered', '2025-08-05'::date, '2025-08-04 13:45:00+00'::timestamptz),
        
        -- Processing orders (pending shipment)
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
        
        -- Cancelled orders (failed shipments)
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

-- =============================================
-- SEED REFUNDS
-- =============================================
INSERT INTO refunds (order_id, amount, currency, status, operation_id, processed_at) VALUES
    -- Completed refunds
    ((SELECT id FROM orders WHERE order_number = '10356'), 149.50, 'USD', 'completed', 'refund-order-10356-149.50', '2025-07-25 10:00:00+00'::timestamptz),
    ((SELECT id FROM orders WHERE order_number = '10501'), 89.99, 'USD', 'completed', 'refund-order-10501-89.99', '2025-07-01 14:30:00+00'::timestamptz),
    ((SELECT id FROM orders WHERE order_number = '10502'), 49.99, 'USD', 'completed', 'refund-order-10502-49.99', '2025-07-02 11:15:00+00'::timestamptz),
    ((SELECT id FROM orders WHERE order_number = '10503'), 219.99, 'USD', 'completed', 'refund-order-10503-219.99', '2025-07-03 09:45:00+00'::timestamptz),
    ((SELECT id FROM orders WHERE order_number = '10504'), 59.99, 'USD', 'completed', 'refund-order-10504-59.99', '2025-07-04 16:20:00+00'::timestamptz),
    ((SELECT id FROM orders WHERE order_number = '10505'), 199.99, 'USD', 'completed', 'refund-order-10505-199.99', '2025-07-05 13:10:00+00'::timestamptz),
    -- Pending refunds (for demo approval workflow)
    ((SELECT id FROM orders WHERE order_number = '10482'), 74.99, 'USD', 'pending', 'refund-order-10482-74.99', NULL),
    ((SELECT id FROM orders WHERE order_number = '10521'), 299.99, 'USD', 'pending', 'refund-order-10521-299.99', NULL),
    ((SELECT id FROM orders WHERE order_number = '10612'), 199.99, 'USD', 'pending', 'refund-order-10612-199.99', NULL)
ON CONFLICT (operation_id) DO NOTHING;

-- =============================================
-- VERIFICATION QUERIES
-- =============================================
-- Run these after seeding to verify data

-- SELECT 'Customers:' as table_name, COUNT(*) as count FROM customers
-- UNION ALL SELECT 'Orders', COUNT(*) FROM orders
-- UNION ALL SELECT 'Shipments', COUNT(*) FROM shipments
-- UNION ALL SELECT 'Refunds', COUNT(*) FROM refunds;

-- -- Key demo orders
-- SELECT o.order_number, o.status, o.total_amount, c.name as customer, s.status as shipment_status
-- FROM orders o
-- JOIN customers c ON c.id = o.customer_id
-- LEFT JOIN shipments s ON s.order_id = o.id
-- WHERE o.order_number IN ('10482', '10521', '10356', '10287', '10612')
-- ORDER BY o.order_number;