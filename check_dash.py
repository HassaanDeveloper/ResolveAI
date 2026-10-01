import urllib.request
try:
    resp = urllib.request.urlopen('http://localhost:3001/dashboard', timeout=5)
    content = resp.read().decode('utf-8')
    print(f"Status: {resp.status}")
    print(f"Content length: {len(content)} bytes")
    if 'Total Requests' in content:
        print("✓ Dashboard metric cards present")
    if 'Pending Approvals' in content:
        print("✓ Pending Approvals card present")
    if 'Not enough data' in content:
        print("✓ 'Not enough data' text present (avg resolution time fix)")
    elif '0s' in content:
        print("✗ Still showing 0s")
    if 'border-l-' in content:
        print("✓ Colored left borders present")
    if 'surface-elevated' in content:
        print("✓ Headline stats present")
    if 'SUCCESS RATE' in content or 'successRate' in content:
        print("✓ Computed headline stats present")
    if 'ArrowRight' in content:
        print("✓ Quick Actions arrows present")
    if 'hover:bg-accent' in content:
        print("✓ Quick Actions hover states present")
    if 'transition-all' in content:
        print("✓ Quick Actions transitions present")
except Exception as e:
    print(f"Error: {e}")
