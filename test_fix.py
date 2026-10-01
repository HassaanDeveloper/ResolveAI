import urllib.request
import json
import sys

def test_endpoint(url, method="GET", data=None):
    try:
        if data:
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json', 'Origin': 'http://localhost:3000'}, method=method)
        else:
            req = urllib.request.Request(url, headers={'Origin': 'http://localhost:3000'}, method=method)
        r = urllib.request.urlopen(req)
        headers = dict(r.headers)
        cors = {k: v for k, v in headers.items() if 'access-control' in k.lower()}
        return r.status, cors
    except urllib.error.HTTPError as e:
        headers = dict(e.headers)
        cors = {k: v for k, v in headers.items() if 'access-control' in k.lower()}
        return e.code, cors
    except Exception as e:
        return str(e), {}

print("=== Testing CORS after fix ===")
status, cors = test_endpoint("http://localhost:8000/api/v1/health")
print(f"GET /health -> Status: {status}, CORS: {cors}")

data = json.dumps({"user_request": "test", "customer_id": "CUST-001", "order_id": "10482"}).encode()
status, cors = test_endpoint("http://localhost:8000/api/v1/resolutions", "POST", data)
print(f"POST /resolutions -> Status: {status}, CORS: {cors}")

status, cors = test_endpoint("http://localhost:8000/api/v1/resolutions/", "POST", data)
print(f"POST /resolutions/ -> Status: {status}, CORS: {cors}")
