import subprocess
import sys
import os
import time

# Start backend
os.chdir(r'E:\ResolveAI\backend')
backend_proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=open(r'E:\ResolveAI\backend\uvicorn.log', 'w'),
    stderr=subprocess.STDOUT
)
print(f"Backend started with PID: {backend_proc.pid}")
time.sleep(2)

# Verify backend
import urllib.request, json
try:
    resp = urllib.request.urlopen('http://localhost:8000/api/v1/dashboard/dashboard/metrics')
    data = json.loads(resp.read())
    print(f"Backend API OK: {json.dumps(data)}")
except Exception as e:
    print(f"Backend API error: {e}")

# Start frontend
os.chdir(r'E:\ResolveAI\frontend')
frontend_proc = subprocess.Popen(
    ['npx', 'next', 'dev'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    env={**os.environ, 'NEXT_DISABLE_TURBOPACK': '1', 'NODE_OPTIONS': '--max-old-space-size=4096'}
)
print(f"Frontend dev server starting with PID: {frontend_proc.pid}")
time.sleep(5)
print("Dev servers running. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    backend_proc.terminate()
    frontend_proc.terminate()
    print("Stopped")
