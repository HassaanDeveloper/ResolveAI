import urllib.request
try:
    resp = urllib.request.urlopen('http://localhost:3001/dashboard')
    content = resp.read().decode('utf-8')
    print(f"Status: {resp.status}")
    print(f"Content length: {len(content)} bytes")
    # Check if the page contains the dashboard content
    if 'dashboard' in content.lower() or 'Total Requests' in content or 'Pending Approvals' in content:
        print("Dashboard page loaded successfully!")
    if 'Not enough data' in content or 'Not enough' in content:
        print("'Not enough data' text found in page")
    # Check for key elements
    checks = {
        'border-l-4': 'border-left stripe',
        'surface-elevated': 'headline stats',
        'MetricCard': 'MetricCard component',
        'ArrowRight': 'Quick Actions arrows',
        'successRate': 'success rate computed',
    }
    for key, desc in checks.items():
        if key in content:
            print(f"Found: {desc} ({key})")
except Exception as e:
    print(f"Error: {e}")
