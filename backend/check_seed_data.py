from app.services.database import get_supabase_client
from collections import Counter
import json

client = get_supabase_client()

# Check orders
result = client.table('orders').select('*').execute()
orders = result.data if result.data else []
print(f"Total orders: {len(orders)}")
print("\nOrders:")
for o in orders:
    print(f"  order_number={o['order_number']}, customer_id={o.get('customer_id','?')[:8]}..., status={o['status']}, total={o['total_amount']}")

# Check customers
cust_result = client.table('customers').select('*').execute()
customers = cust_result.data if cust_result.data else []
print(f"\nTotal customers: {len(customers)}")
print("\nCustomers (first 5):")
for c in customers[:5]:
    print(f"  external_customer_id={c['external_customer_id']}, name={c['name']}")

# Check shipments
ship_result = client.table('shipments').select('*').execute()
shipments = ship_result.data if ship_result.data else []
print(f"\nTotal shipments: {len(shipments)}")
if shipments:
    print("\nShipments (first 5):")
    for s in shipments[:5]:
        print(f"  order_id={s.get('order_id','?')}, tracking={s.get('tracking_number','?')}, status={s['status']}")
