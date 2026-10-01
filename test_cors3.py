import urllib.request
import json

# Test POST to /api/v1/resolutions with detailed header inspection
print("=== POST /api/v1/resolutions - Full Headers ===")
data = json.dumps({"user_request": "test", "customer_id": "CUST-001", "order_id": "10482"}).encode()
req = urllib.request.Request(
    'http://localhost:8000/api/v1/resolutions',
    data=data,
    headers={'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'},
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print("Response headers:")
    for k, v in e.headers.items():
        print(f"  {k}: {v}")
    has_cors = any('access-control' in k.lower() for k in e.headers)
    print(f"\nHas CORS headers: {has_cors}")
except Exception as e:
    print(f"Error: {e}")

# Test GET to /api/v1/health - Full Headers (should work)
print("\n=== GET /api/v1/health - Full Headers ===")
try:
    r = urllib.request.urlopen('http://localhost:8000/api/v1/health')
    print(f"Status: {r.status}")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"Error: {e}")

# Test the trailing slash redirect
print("\n=== POST /api/v1/resolutions/ - Full Headers ===")
req = urllib.request.Request(
    'http://localhost:8000/api/v1/resolutions/',
    data=data,
    headers={'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'},
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    has_cors = any('access-control' in k.lower() for k in r.headers)
    print(f"Has CORS headers: {has_cors}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    has_cors = any('access-control' in k.lower() for k in e.headers)
    print(f"Has CORS headers: {has_cors}")
    print(f"Location header: {e.headers.get('Location', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")
