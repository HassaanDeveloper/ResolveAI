import subprocess
import sys
import os
import time
import urllib.request

os.chdir(r'E:\ResolveAI\frontend')
proc = subprocess.Popen(
    ['npx', 'next', 'dev', '--port', '3001'],
    stdout=open(r'E:\ResolveAI\frontend\devserver.log', 'w'),
    stderr=subprocess.STDOUT
)
print(f"Frontend dev server starting with PID: {proc.pid}")
time.sleep(5)

# Check if it's running
try:
    resp = urllib.request.urlopen('http://localhost:3001/dashboard', timeout=5)
    content = resp.read().decode('utf-8')
    print(f"Status: {resp.status}")
    print(f"Content length: {len(content)} bytes")
    if 'Total Requests' in content or 'Pending' in content:
        print("Dashboard page loaded successfully!")
    if 'Not enough data' in content:
        print("'Not enough data' text found!")
    if 'border-l-' in content or 'surface-elevated' in content:
        print("Visual enhancements present in HTML!")
    if 'successRate' in content or 'SUCCESS RATE' in content:
        print("Headline stats present!")
except Exception as e:
    print(f"Could not fetch page yet: {e}")

print("\nDev server running. Checking log...")
time.sleep(3)
with open(r'E:\ResolveAI\frontend\devserver.log') as f:
    log_content = f.read()
    # Print last 20 lines
    lines = log_content.strip().split('\n')
    for line in lines[-20:]:
        print(line)
