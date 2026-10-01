import httpx
from app.core.config import settings

# Create exec_sql function and apply migration via HTTP calls
url = settings.SUPABASE_URL
key = settings.SUPABASE_SERVICE_KEY

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

# First, try to create exec_sql function
create_function_sql = """
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS SETOF jsonb
LANGUAGE plpgsql
AS $$
DECLARE
    result jsonb;
BEGIN
    EXECUTE sql;
    GET DIAGNOSTICS result = ROW_COUNT;
    RETURN NEXT jsonb_build_object('rows_affected', result);
    RETURN;
END;
$$;
"""

print("Creating exec_sql function...")
try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": create_function_sql},
        timeout=30.0,
    )
    print(f"Create function response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error creating function: {e}")

# Now apply the workflow state columns migration
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

print("\nApplying resolutions table migration...")
try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": alter_resolutions},
        timeout=30.0,
    )
    print(f"Resolutions migration response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error applying resolutions migration: {e}")

print("\nApplying documents table migration...")
try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": alter_documents},
        timeout=30.0,
    )
    print(f"Documents migration response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error applying documents migration: {e}")

print("\nDone!")