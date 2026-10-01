# ResolveAI Database Schema Documentation

## Overview

This document describes the PostgreSQL schema for ResolveAI, designed for Supabase with pgvector support.

## Core Tables

### customers
Synthetic customer records for Northstar Commerce.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| external_customer_id | VARCHAR(100) | NOT NULL, UNIQUE | Business-facing customer ID |
| name | VARCHAR(255) | NOT NULL | Customer name |
| email | VARCHAR(255) | NOT NULL | Customer email |
| account_status | customer_account_status | NOT NULL, DEFAULT 'active' | Enum: active, suspended, closed |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Indexes:** `idx_customers_external_id`, `idx_customers_email`

---

### orders
Synthetic order records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| order_number | VARCHAR(50) | NOT NULL, UNIQUE | Business-facing order number (e.g., "10482") |
| customer_id | UUID | NOT NULL, FK → customers(id) | Customer reference |
| status | order_status | NOT NULL, DEFAULT 'pending' | Enum: pending, processing, shipped, delivered, cancelled, refunded |
| total_amount | DECIMAL(10,2) | NOT NULL, CHECK >= 0 | Order total |
| currency | CHAR(3) | NOT NULL, DEFAULT 'USD' | ISO currency code |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update (auto via trigger) |

**Indexes:** `idx_orders_customer_id`, `idx_orders_order_number`, `idx_orders_status`

---

### shipments
Shipment tracking information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| order_id | UUID | NOT NULL, FK → orders(id) CASCADE | Order reference |
| carrier | VARCHAR(100) | NOT NULL | Carrier name (e.g., "FedEx", "UPS") |
| tracking_number | VARCHAR(100) | NOT NULL | Carrier tracking number |
| status | shipment_status | NOT NULL, DEFAULT 'pending' | Enum: pending, in_transit, delayed, delivered, failed |
| estimated_delivery_date | DATE | | Estimated delivery |
| delivered_at | TIMESTAMPTZ | | Actual delivery timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update (auto via trigger) |

**Indexes:** `idx_shipments_order_id`, `idx_shipments_tracking_number`, `idx_shipments_status`

---

### refunds
Refund requests and processing records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| order_id | UUID | NOT NULL, FK → orders(id) RESTRICT | Order reference |
| amount | DECIMAL(10,2) | NOT NULL, CHECK > 0 | Refund amount |
| currency | CHAR(3) | NOT NULL, DEFAULT 'USD' | ISO currency code |
| status | refund_status | NOT NULL, DEFAULT 'pending' | Enum: pending, approved, processing, completed, rejected, failed |
| operation_id | VARCHAR(100) | NOT NULL, UNIQUE | Idempotency key (e.g., "refund-order-10482-74.99") |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| processed_at | TIMESTAMPTZ | | Processing completion timestamp |

**Indexes:** `idx_refunds_order_id`, `idx_refunds_operation_id`, `idx_refunds_status`

---

### resolutions
Operational resolution requests — the main workflow entity.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| request_id | VARCHAR(100) | NOT NULL, UNIQUE | Request correlation ID (matches X-Request-ID) |
| user_request | TEXT | NOT NULL | Original user request text |
| intent | VARCHAR(100) | | Classified intent (e.g., "refund_request", "cancellation") |
| status | resolution_status | NOT NULL, DEFAULT 'pending' | Enum: pending, investigating, policy_check, pending_approval, executing, verifying, completed, rejected, failed |
| customer_id | UUID | FK → customers(id) SET NULL | Optional customer reference |
| order_id | UUID | FK → orders(id) SET NULL | Optional order reference |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update (auto via trigger) |

**Indexes:** `idx_resolutions_request_id`, `idx_resolutions_customer_id`, `idx_resolutions_order_id`, `idx_resolutions_status`

---

### approval_requests
Human approval requests for high-risk actions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| resolution_id | UUID | NOT NULL, FK → resolutions(id) CASCADE | Resolution reference |
| action_type | operation_type | NOT NULL | Enum: issue_refund, cancel_order, create_escalation |
| action_payload | JSONB | NOT NULL | Structured action parameters |
| reason | TEXT | NOT NULL | Why approval is required |
| status | approval_status | NOT NULL, DEFAULT 'pending' | Enum: pending, approved, rejected |
| requested_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Request timestamp |
| decided_at | TIMESTAMPTZ | | Decision timestamp |
| decided_by | VARCHAR(100) | | Approver identifier (placeholder for MVP) |

**Indexes:** `idx_approval_requests_resolution_id`, `idx_approval_requests_status`

---

### audit_events
Immutable audit trail of all workflow events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| request_id | VARCHAR(100) | NOT NULL | Request correlation ID |
| resolution_id | UUID | FK → resolutions(id) SET NULL | Optional resolution reference |
| event_type | audit_event_type | NOT NULL | Enum: request_received, intent_identified, order_retrieved, shipment_checked, policy_retrieved, refund_calculated, policy_evaluated, approval_requested, approval_granted, approval_rejected, action_executed, action_verified, workflow_completed, workflow_failed, error_occurred |
| event_data | JSONB | NOT NULL, DEFAULT '{}' | Structured event payload |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Event timestamp |

**Indexes:** `idx_audit_events_request_id`, `idx_audit_events_resolution_id`, `idx_audit_events_created_at`

---

### operations
Idempotency tracking for side-effect operations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| operation_id | VARCHAR(100) | PK | Unique operation identifier |
| operation_type | operation_type | NOT NULL | Enum: issue_refund, cancel_order, create_escalation |
| status | operation_status | NOT NULL, DEFAULT 'pending' | Enum: pending, executed, failed, duplicate |
| result | JSONB | | Operation result payload |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update (auto via trigger) |

**Indexes:** `idx_operations_type`, `idx_operations_status`

---

## RAG / Knowledge Document Tables

### documents
Company policy documents for RAG ingestion.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| name | VARCHAR(255) | NOT NULL | Document name (e.g., "Refund Policy v2.1") |
| source | VARCHAR(255) | | Source system or file path |
| version | VARCHAR(50) | | Document version |
| content | TEXT | NOT NULL | Full document text |
| metadata | JSONB | DEFAULT '{}' | Additional metadata |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Indexes:** `idx_documents_name`

---

### document_chunks
Document chunks with embeddings for vector search.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Primary key |
| document_id | UUID | NOT NULL, FK → documents(id) CASCADE | Document reference |
| chunk_index | INTEGER | NOT NULL | Sequential chunk number |
| content | TEXT | NOT NULL | Chunk text content |
| embedding | vector(768) | | **Dimension: 768 for Gemini text-embedding-004** |
| metadata | JSONB | DEFAULT '{}' | Chunk metadata (section, page, etc.) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Indexes:** `idx_document_chunks_document_id`
**Planned:** `idx_document_chunks_embedding` (HNSW, created after data insertion)

---

## Enums

| Enum | Values |
|------|--------|
| customer_account_status | active, suspended, closed |
| order_status | pending, processing, shipped, delivered, cancelled, refunded |
| shipment_status | pending, in_transit, delayed, delivered, failed |
| refund_status | pending, approved, processing, completed, rejected, failed |
| resolution_status | pending, investigating, policy_check, pending_approval, executing, verifying, completed, rejected, failed |
| approval_status | pending, approved, rejected |
| audit_event_type | request_received, intent_identified, order_retrieved, shipment_checked, policy_retrieved, refund_calculated, policy_evaluated, approval_requested, approval_granted, approval_rejected, action_executed, action_verified, workflow_completed, workflow_failed, error_occurred |
| operation_type | issue_refund, cancel_order, create_escalation |
| operation_status | pending, executed, failed, duplicate |

---

## Triggers

- `update_updated_at_column()` — Updates `updated_at` on row modification for: orders, shipments, resolutions, operations

---

## Vector Dimension Note

The `document_chunks.embedding` column uses `vector(768)` which matches **Gemini text-embedding-004** (768 dimensions).

If a different embedding model is chosen, update the migration:
```sql
ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(<NEW_DIMENSION>);
```

---

## Applying Migrations in Supabase

1. Open Supabase Dashboard → SQL Editor
2. Copy the contents of `backend/migrations/001_initial_schema.sql`
3. Paste and run in the SQL Editor
4. Verify tables created: `SELECT * FROM information_schema.tables WHERE table_schema = 'public';`
5. For vector index (after data insertion):
   ```sql
   CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
   ```