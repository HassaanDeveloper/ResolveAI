from app.services.database import get_supabase_client
client = get_supabase_client()

# Apply migration directly using raw SQL execution
# We need to execute the ALTER TABLE statements

alter_resolutions = """
ALTER TABLE resolutions 
ADD COLUMN IF NOT EXISTS retrieved_documents JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS tool_calls JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS policy_result JSONB,
ADD COLUMN IF NOT EXISTS approval JSONB,
ADD COLUMN IF NOT EXISTS action_result JSONB,
ADD COLUMN IF NOT EXISTS verification JSONB,
ADD COLUMN IF NOT EXISTS final_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS errors JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
"""

alter_documents = """
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS error TEXT,
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;
"""

# Try using a raw query approach
try:
    # Supabase doesn't have a direct exec_sql, let's try using the REST API directly
    # or use a different approach
    import httpx
    
    # Get the Supabase URL and key from settings
    from app.core.config import settings
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Try to execute via the pg REST API - this won't work for DDL
    # We need to use the Supabase Management API or SQL Editor
    
    print("Cannot execute DDL via REST API directly")
    print("Need to run migration in Supabase SQL Editor manually")
    
except Exception as e:
    print(f"Error: {e}")

print("Migration SQL ready - apply via Supabase Dashboard SQL Editor:")
print("---")
print(alter_resolutions)
print("---")
print(alter_documents)