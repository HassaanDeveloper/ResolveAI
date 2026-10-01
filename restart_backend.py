import subprocess
import sys
import os

# Kill existing python processes
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
import time
time.sleep(1)

# Start new backend
os.chdir(r'E:\ResolveAI\backend')
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=open(r'E:\ResolveAI\backend\uvicorn.log', 'w'),
    stderr=subprocess.STDOUT
)
print(f"Backend started with PID: {proc.pid}")
print("Waiting 2 seconds...")
time.sleep(2)
print("Done")
