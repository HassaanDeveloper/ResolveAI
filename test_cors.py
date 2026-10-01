import urllib.request
import json

# Test CORS preflight
print("=== CORS Preflight ===")
req = urllib.request.Request(
    'http://localhost:8000/api/v1/resolutions',
    method='OPTIONS',
    headers={
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
)
try:
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    print(f"Headers: {dict(r.headers)}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Headers: {dict(e.headers)}")

# Test POST with Origin header
print("\n=== POST with Origin ===")
data = json.dumps({"user_request": "test", "customer_id": "CUST-001", "order_id": "10482"}).encode()
req = urllib.request.Request(
    'http://localhost:8000/api/v1/resolutions',
    data=data,
    headers={
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
    },
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    print(f"CORS Headers: {[k for k in r.headers.keys() if 'access' in k.lower() or 'cors' in k.lower()]}")
    print(r.read().decode()[:200])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    cors_headers = [k for k in e.headers.keys() if 'access' in k.lower() or 'cors' in k.lower()]
    print(f"CORS Headers: {cors_headers}")
    print(e.read().decode()[:200])
except Exception as e:
    print(f"Error: {e}")
