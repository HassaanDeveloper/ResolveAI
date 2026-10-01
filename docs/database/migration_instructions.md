# Supabase Migration Instructions

## Prerequisites

1. Create a Supabase project at https://supabase.com
2. Note your project URL and service role key (from Project Settings → API)
3. Update `.env` with your credentials (copy from `.env.example`)

## Applying the Initial Schema

### Option 1: Supabase SQL Editor (Recommended)

1. Go to your Supabase Dashboard → SQL Editor
2. Click "New Query"
3. Copy the entire contents of `backend/migrations/001_initial_schema.sql`
4. Paste into the editor
5. Click "Run" (or press Ctrl/Cmd + Enter)
6. Verify success — you should see "Success. No rows returned"

### Option 2: Supabase CLI (Local Development)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Push migration
supabase db push
```

## Verifying the Schema

Run this query in SQL Editor to confirm all tables exist:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Expected tables:
- approval_requests
- audit_events
- customers
- document_chunks
- documents
- operations
- orders
- refunds
- resolutions
- shipments

## Enabling pgvector

pgvector is enabled by default in Supabase. Verify with:

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

If not present, run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Creating the Vector Index (After Data Insertion)

The HNSW index for vector similarity search should be created **after** inserting document chunks for better performance:

```sql
CREATE INDEX idx_document_chunks_embedding ON document_chunks
USING hnsw (embedding vector_cosine_ops);
```

## Row Level Security (RLS)

RLS is disabled by default in the migration. To enable for production:

```sql
-- Enable RLS on tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
-- ... etc for other tables

-- Create policies (example for customers)
CREATE POLICY "Allow read access" ON customers
    FOR SELECT USING (true);

-- For service role (backend), use service role key which bypasses RLS
```

## Updating Vector Dimension

If the embedding model changes (e.g., different Gemini model), update the vector dimension:

```sql
-- Check current dimension
SELECT column_name, udt_name, atttypmod
FROM information_schema.columns
WHERE table_name = 'document_chunks' AND column_name = 'embedding';

-- Alter column (requires dropping index first if exists)
DROP INDEX IF EXISTS idx_document_chunks_embedding;
ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(<NEW_DIM>);
-- Recreate index after data insertion
```

## Environment Variables

Add to your `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

The service role key bypasses RLS and should only be used on the backend.

## Troubleshooting

### "relation does not exist" errors
- Ensure migration ran completely
- Check for syntax errors in SQL Editor output

### "vector type not found"
- Run `CREATE EXTENSION IF NOT EXISTS vector;`

### Permission denied
- Use service role key (not anon key) for backend operations
- Service role key bypasses RLS

### Vector dimension mismatch
- Verify embedding model dimension matches `vector(N)` in schema
- Update migration and re-run if needed