-- ResolveAI Synthetic Customer Data
-- Part 04: Synthetic Northstar Commerce Data
-- Run this in Supabase SQL Editor AFTER 001_initial_schema.sql

-- =============================================
-- CUSTOMERS (25 synthetic customers)
-- =============================================

-- Using ON CONFLICT DO NOTHING for idempotent seeding
-- external_customer_id is the business key

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