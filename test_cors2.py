import urllib.request
import json

# Test GET /api/v1/health (should work)
print("=== GET /api/v1/health ===")
try:
    r = urllib.request.urlopen('http://localhost:8000/api/v1/health')
    cors_headers = {k: v for k, v in r.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"Status: {r.status}")
    print(f"CORS Headers: {cors_headers}")
except Exception as e:
    print(f"Error: {e}")

# Test GET /api/v1/dashboard/dashboard/metrics (should work)
print("\n=== GET /api/v1/dashboard/dashboard/metrics ===")
try:
    r = urllib.request.urlopen('http://localhost:8000/api/v1/dashboard/dashboard/metrics')
    cors_headers = {k: v for k, v in r.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"Status: {r.status}")
    print(f"CORS Headers: {cors_headers}")
except urllib.error.HTTPError as e:
    cors_headers = {k: v for k, v in e.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"HTTP Error: {e.code}")
    print(f"CORS Headers: {cors_headers}")
except Exception as e:
    print(f"Error: {e}")

# Test POST /api/v1/resolutions - check CORS headers on error response
print("\n=== POST /api/v1/resolutions (500 error) ===")
data = json.dumps({"user_request": "test", "customer_id": "CUST-001", "order_id": "10482"}).encode()
req = urllib.request.Request(
    'http://localhost:8000/api/v1/resolutions',
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    cors_headers = {k: v for k, v in r.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"Status: {r.status}")
    print(f"CORS Headers: {cors_headers}")
except urllib.error.HTTPError as e:
    cors_headers = {k: v for k, v in e.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"HTTP Error: {e.code}")
    print(f"CORS Headers: {cors_headers}")
    print(f"All headers: {dict(e.headers)}")
except Exception as e:
    print(f"Error: {e}")

# Test POST with trailing slash
print("\n=== POST /api/v1/resolutions/ (307 redirect) ===")
req = urllib.request.Request(
    'http://localhost:8000/api/v1/resolutions/',
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    cors_headers = {k: v for k, v in r.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"Status: {r.status}")
    print(f"CORS Headers: {cors_headers}")
except urllib.error.HTTPError as e:
    cors_headers = {k: v for k, v in e.headers.items() if 'access' in k.lower() or 'cors' in k.lower()}
    print(f"HTTP Error: {e.code}")
    print(f"CORS Headers: {cors_headers}")
except Exception as e:
    print(f"Error: {e}")
