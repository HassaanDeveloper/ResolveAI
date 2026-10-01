import sys
sys.path.insert(0, r'E:\ResolveAI\backend')
from app.api.routes import resolutions, approvals, dashboard, health

print("=== Resolutions Router Routes ===")
for route in resolutions.router.routes:
    print(f"Path: {route.path!r}, Methods: {route.methods}")

print("\n=== Approvals Router Routes ===")
for route in approvals.router.routes:
    print(f"Path: {route.path!r}, Methods: {route.methods}")

print("\n=== Dashboard Router Routes ===")
for route in dashboard.router.routes:
    print(f"Path: {route.path!r}, Methods: {route.methods}")

print("\n=== Health Router Routes ===")
for route in health.router.routes:
    print(f"Path: {route.path!r}, Methods: {route.methods}")
