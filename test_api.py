import urllib.request
import json

base = "http://localhost:8000/api/v1"

# Test health
print("=== Health ===")
try:
    r = urllib.request.urlopen(f"{base}/health")
    print(f"Status: {r.status}")
    print(r.read().decode())
except Exception as e:
    print(f"Error: {e}")

# Test POST to /resolutions (no trailing slash)
print("\n=== POST /resolutions (no slash) ===")
try:
    data = json.dumps({"user_request": "test", "customer_id": "CUST-001", "order_id": "10482"}).encode()
    req = urllib.request.Request(f"{base}/resolutions", data=data, headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"Error: {e}")

# Test POST to /resolutions/ (with trailing slash)
print("\n=== POST /resolutions/ (with slash) ===")
try:
    data = json.dumps({"user_request": "test", "customer_id": "CUST-001", "order_id": "10482"}).encode()
    req = urllib.request.Request(f"{base}/resolutions/", data=data, headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"Error: {e}")

# Test GET to /resolutions (no trailing slash)
print("\n=== GET /resolutions (no slash) ===")
try:
    req = urllib.request.Request(f"{base}/resolutions", method="GET")
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"Error: {e}")

# Test GET to /resolutions/ (with trailing slash)
print("\n=== GET /resolutions/ (with slash) ===")
try:
    req = urllib.request.Request(f"{base}/resolutions/", method="GET")
    r = urllib.request.urlopen(req)
    print(f"Status: {r.status}")
    print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"Error: {e}")
