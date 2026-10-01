# Synthetic Data Seeding Instructions

## Overview

This document explains how to seed the ResolveAI database with synthetic Northstar Commerce data for development and testing.

## Data Summary

| Entity | Count | Description |
|--------|-------|-------------|
| Customers | 25 | Synthetic customer records |
| Orders | 40 | Orders across all statuses |
| Shipments | ~38 | Shipment tracking for orders |
| Refunds | 9 | Completed + pending refunds |

## Key Demonstration Orders

| Order # | Customer | Status | Amount | Scenario |
|---------|----------|--------|--------|----------|
| **10482** | Sarah Mitchell (CUST-001) | shipped | $74.99 | **Delayed/not arrived - Low-risk refund** (auto-approve) |
| **10521** | James Chen (CUST-002) | shipped | $299.99 | **High-value refund** (requires approval) |
| **10356** | Maria Rodriguez (CUST-003) | refunded | $149.50 | **Already refunded** |
| **10287** | David Thompson (CUST-004) | delivered | $89.99 | **Delivered >30 days ago** (outside policy) |
| **10612** | Jennifer Park (CUST-005) | shipped | $199.99 | **Shipped - cancellation escalation** |

## Seeding Methods

### Method 1: Supabase SQL Editor (Recommended)

1. Open Supabase Dashboard → SQL Editor
2. Copy contents of `backend/seeds/seed_all.sql`
3. Paste and click **Run**
4. Verify with the verification queries at the bottom of the file

### Method 2: Individual Seed Files (For Debugging)

Run in order:
1. `backend/seeds/seed_customers.sql`
2. `backend/seeds/seed_orders.sql`
3. `backend/seeds/seed_shipments.sql`
4. `backend/seeds/seed_refunds.sql`

### Method 3: Python Seed Runner (Programmatic)

```bash
# Install supabase client
pip install supabase httpx

# Configure .env with real credentials
cp .env.example .env
# Edit .env with your SUPABASE_URL and SUPABASE_SERVICE_KEY

# Run
cd backend/seeds
python run_seeds.py
```

## Idempotency

All seed scripts use `ON CONFLICT DO NOTHING` on unique constraints:
- `customers.external_customer_id`
- `orders.order_number`
- `refunds.operation_id`
- Shipments: checked via `NOT EXISTS` on `(order_id, tracking_number)`

**Safe to re-run** — duplicates will be skipped.

## Verification

After seeding, run these queries in SQL Editor:

```sql
-- Count all tables
SELECT 'Customers' as table_name, COUNT(*) FROM customers
UNION ALL SELECT 'Orders', COUNT(*) FROM orders
UNION ALL SELECT 'Shipments', COUNT(*) FROM shipments
UNION ALL SELECT 'Refunds', COUNT(*) FROM refunds;

-- Verify key demo orders
SELECT 
    o.order_number,
    o.status as order_status,
    o.total_amount,
    c.name as customer,
    c.external_customer_id,
    s.status as shipment_status,
    s.tracking_number,
    s.estimated_delivery_date,
    r.status as refund_status,
    r.amount as refund_amount
FROM orders o
JOIN customers c ON c.id = o.customer_id
LEFT JOIN shipments s ON s.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE o.order_number IN ('10482', '10521', '10356', '10287', '10612')
ORDER BY o.order_number;
```

Expected output:
```
 table_name | count
------------+-------
 Customers  |    25
 Orders     |    40
 Shipments  |    38
 Refunds    |     9

 order_number | order_status | total_amount |     customer      | external_customer_id | shipment_status |    tracking_number    | estimated_delivery_date | refund_status | refund_amount
--------------+--------------+--------------+-------------------+----------------------+-----------------+-----------------------+-------------------------+---------------+---------------
 10287        | delivered    |        89.99 | David Thompson    | CUST-004             | delivered       | FX987654321US         | 2025-06-15              |               |
 10356        | refunded     |       149.50 | Maria Rodriguez   | CUST-003             | delivered       | 9400100000000000000000| 2025-07-20              | completed     |        149.50
 10482        | shipped      |        74.99 | Sarah Mitchell    | CUST-001             | delayed         | FX123456789US         | 2025-08-15              | pending       |         74.99
 10521        | shipped      |       299.99 | James Chen        | CUST-002             | in_transit      | 1Z999AA10123456784    | 2025-09-10              | pending       |       299.99
 10612        | shipped      |       199.99 | Jennifer Park     | CUST-005             | in_transit      | 1Z999AA10123456785    | 2025-09-12              | pending       |       199.99
```

## Data Characteristics

### Customers
- 25 records with realistic names/emails
- 3 account statuses: active (22), suspended (1), closed (1)
- External IDs: CUST-001 through CUST-025

### Orders
- 40 orders spanning all statuses:
  - pending: 1
  - processing: 5
  - shipped: 11 (5 demo + 6 regular)
  - delivered: 15
  - cancelled: 5
  - refunded: 6 (1 demo + 5 regular)
- Amounts: $49.99 – $349.99
- Currency: USD

### Shipments
- Carriers: FedEx, UPS, USPS
- Statuses: pending, in_transit, delayed, delivered, failed
- Realistic tracking number formats per carrier
- Delivered shipments have `delivered_at` timestamps

### Refunds
- 6 completed refunds (historical)
- 3 pending refunds (for approval workflow demo):
  - 10482: $74.99 (auto-approve, ≤$100)
  - 10521: $299.99 (requires approval, >$100)
  - 10612: $199.99 (requires approval, >$100)
- All have unique `operation_id` for idempotency

## Resetting Data

To completely reset and re-seed:

```sql
-- In Supabase SQL Editor (run in order)
TRUNCATE refunds, shipments, orders, customers RESTART IDENTITY CASCADE;
-- Then re-run seed_all.sql
```

Or drop and recreate schema:
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Then run 001_initial_schema.sql + seed_all.sql
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "relation does not exist" | Run `001_initial_schema.sql` first |
| "duplicate key value violates unique constraint" | Scripts are idempotent — safe to re-run |
| "permission denied" | Use `SUPABASE_SERVICE_KEY` (not anon key) |
| Foreign key violations | Ensure seeding order: customers → orders → shipments/refunds |
| Python runner fails | Check `.env` credentials; install `supabase` and `httpx` |