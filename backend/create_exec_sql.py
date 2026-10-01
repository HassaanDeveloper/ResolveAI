from app.services.database import get_supabase_client
client = get_supabase_client()

# Create exec_sql function first
create_function = """
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

# Try to create the function
import httpx
from app.core.config import settings

url = settings.SUPABASE_URL
key = settings.SUPABASE_SERVICE_KEY

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"sql": create_function},
        timeout=30.0,
    )
    print(f"Create function response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error creating function: {e}")