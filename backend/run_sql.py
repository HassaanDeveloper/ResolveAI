import httpx
from app.core.config import settings

url = settings.SUPABASE_URL
key = settings.SUPABASE_SERVICE_KEY

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

# Try the pg endpoint for raw SQL
# Some Supabase instances expose a pg endpoint
sql = "ALTER TYPE operation_status ADD VALUE 'executing';"

try:
    response = httpx.post(
        f"{url}/rest/v1/rpc/query",
        headers=headers,
        json={"query": sql},
        timeout=30.0,
    )
    print(f"Response: {response.status_code}")
    print(f"Text: {response.text}")
except Exception as e:
    print(f"Error with query endpoint: {e}")

# Try using the pgrst endpoint
try:
    response = httpx.post(
        f"{url}/rest/v1/",
        headers={**headers, "Prefer": "params=single-object"},
        json={"query": sql},
        timeout=30.0,
    )
    print(f"REST response: {response.status_code}")
    print(f"Text: {response.text}")
except Exception as e:
    print(f"Error with REST: {e}")