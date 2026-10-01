-- ResolveAI Database Schema Migration
-- Part 03: Supabase Database Architecture
-- Apply this migration in Supabase SQL Editor

-- =============================================
-- EXTENSIONS
-- =============================================

-- Enable pgvector for embedding storage (when needed)
-- Note: pgvector is enabled by default in Supabase
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- ENUMS
-- =============================================

-- Customer account status
CREATE TYPE customer_account_status AS ENUM ('active', 'suspended', 'closed');

-- Order status
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded');

-- Shipment status
CREATE TYPE shipment_status AS ENUM ('pending', 'in_transit', 'delayed', 'delivered', 'failed');

-- Refund status
CREATE TYPE refund_status AS ENUM ('pending', 'approved', 'processing', 'completed', 'rejected', 'failed');

-- Resolution status
CREATE TYPE resolution_status AS ENUM ('pending', 'investigating', 'policy_check', 'pending_approval', 'executing', 'verifying', 'completed', 'rejected', 'failed');

-- Approval request status
CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected');

-- Audit event types
CREATE TYPE audit_event_type AS ENUM (
    'request_received',
    'intent_identified',
    'order_retrieved',
    'shipment_checked',
    'policy_retrieved',
    'refund_calculated',
    'policy_evaluated',
    'approval_requested',
    'approval_granted',
    'approval_rejected',
    'action_executed',
    'action_verified',
    'workflow_completed',
    'workflow_failed',
    'error_occurred'
);

-- Operation types (for idempotency)
CREATE TYPE operation_type AS ENUM ('issue_refund', 'cancel_order', 'create_escalation');

-- Operation status
CREATE TYPE operation_status AS ENUM ('pending', 'executed', 'failed', 'duplicate');

-- =============================================
-- CORE TABLES
-- =============================================

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_customer_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    account_status customer_account_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_external_id ON customers(external_customer_id);
CREATE INDEX idx_customers_email ON customers(email);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    status order_status NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_status ON orders(status);

-- Shipments table
CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    carrier VARCHAR(100) NOT NULL,
    tracking_number VARCHAR(100) NOT NULL,
    status shipment_status NOT NULL DEFAULT 'pending',
    estimated_delivery_date DATE,
    delivered_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_shipments_order_id ON shipments(order_id);
CREATE INDEX idx_shipments_tracking_number ON shipments(tracking_number);
CREATE INDEX idx_shipments_status ON shipments(status);

-- Refunds table
CREATE TABLE refunds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    status refund_status NOT NULL DEFAULT 'pending',
    operation_id VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_refunds_order_id ON refunds(order_id);
CREATE INDEX idx_refunds_operation_id ON refunds(operation_id);
CREATE INDEX idx_refunds_status ON refunds(status);

-- Resolutions table (operational resolution requests)
CREATE TABLE resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) NOT NULL UNIQUE,
    user_request TEXT NOT NULL,
    intent VARCHAR(100),
    status resolution_status NOT NULL DEFAULT 'pending',
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_resolutions_request_id ON resolutions(request_id);
CREATE INDEX idx_resolutions_customer_id ON resolutions(customer_id);
CREATE INDEX idx_resolutions_order_id ON resolutions(order_id);
CREATE INDEX idx_resolutions_status ON resolutions(status);

-- Approval requests table
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resolution_id UUID NOT NULL REFERENCES resolutions(id) ON DELETE CASCADE,
    action_type operation_type NOT NULL,
    action_payload JSONB NOT NULL,
    reason TEXT NOT NULL,
    status approval_status NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMPTZ,
    decided_by VARCHAR(100)
);

CREATE INDEX idx_approval_requests_resolution_id ON approval_requests(resolution_id);
CREATE INDEX idx_approval_requests_status ON approval_requests(status);

-- Audit events table
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(100) NOT NULL,
    resolution_id UUID REFERENCES resolutions(id) ON DELETE SET NULL,
    event_type audit_event_type NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_events_request_id ON audit_events(request_id);
CREATE INDEX idx_audit_events_resolution_id ON audit_events(resolution_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at);

-- Operations table (for idempotency)
CREATE TABLE operations (
    operation_id VARCHAR(100) PRIMARY KEY,
    operation_type operation_type NOT NULL,
    status operation_status NOT NULL DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operations_type ON operations(operation_type);
CREATE INDEX idx_operations_status ON operations(status);

-- =============================================
-- RAG / KNOWLEDGE DOCUMENT TABLES (Prepared for Part 08)
-- =============================================

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source VARCHAR(255),
    version VARCHAR(50),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_name ON documents(name);

-- Document chunks table
-- Note: Vector dimension is a placeholder (1536 = OpenAI text-embedding-3-small)
-- Will be updated to match Gemini embedding dimension (768 for text-embedding-004) in Part 08
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    -- Embedding vector - dimension will be set when Gemini embeddings are configured
    -- Using 768 as placeholder for Gemini text-embedding-004
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);

-- Vector similarity search index (HNSW) - create after data insertion for better performance
-- CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- =============================================
-- UPDATED_AT TRIGGER FUNCTION
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipments_updated_at BEFORE UPDATE ON shipments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resolutions_updated_at BEFORE UPDATE ON resolutions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_operations_updated_at BEFORE UPDATE ON operations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- ROW LEVEL SECURITY (RLS) - Optional, can be enabled later
-- =============================================

-- ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE refunds ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE resolutions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE operations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- =============================================
-- COMMENTS
-- =============================================

COMMENT ON TABLE customers IS 'Synthetic customer records for Northstar Commerce';
COMMENT ON TABLE orders IS 'Synthetic order records';
COMMENT ON TABLE shipments IS 'Shipment tracking information';
COMMENT ON TABLE refunds IS 'Refund requests and processing records';
COMMENT ON TABLE resolutions IS 'Operational resolution requests (the main workflow entity)';
COMMENT ON TABLE approval_requests IS 'Human approval requests for high-risk actions';
COMMENT ON TABLE audit_events IS 'Immutable audit trail of all workflow events';
COMMENT ON TABLE operations IS 'Idempotency tracking for side-effect operations';
COMMENT ON TABLE documents IS 'Company policy documents for RAG';
COMMENT ON TABLE document_chunks IS 'Document chunks with embeddings for vector search';