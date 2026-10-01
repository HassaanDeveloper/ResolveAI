import httpx
from app.core.config import settings

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

# Now add executing to operation_status enum
alter_enum = """
ALTER TYPE operation_status ADD VALUE 'executing';
"""

print("\nAdding 'executing' to operation_status enum...")
try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": alter_enum},
        timeout=30.0,
    )
    print(f"Enum migration response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error applying enum migration: {e}")

# Verify
verify_sql = """
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'operation_status'::regtype ORDER BY enumsortorder;
"""

print("\nVerifying enum values...")
try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": verify_sql},
        timeout=30.0,
    )
    print(f"Verify response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error verifying: {e}")

print("\nDone!")