import subprocess, os, sys, time

# Kill all python
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
time.sleep(1)

# Start backend
os.chdir(r'E:\ResolveAI\backend')
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(2)

# Verify
import socket
s = socket.socket()
s.settimeout(2)
result = s.connect_ex(('localhost', 8000))
s.close()
if result == 0:
    print("Backend is running on port 8000")
else:
    print("Backend FAILED to start")
