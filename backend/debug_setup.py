from app.services.database import get_supabase_client
from evaluation.integration.fixtures import TEST_CUSTOMERS, TEST_ORDERS, _RUNTIME_IDS
from app.core.config import settings

client = get_supabase_client()

# Clear runtime IDs
_RUNTIME_IDS['customers'].clear()
_RUNTIME_IDS['orders'].clear()

# Insert customers
for customer in TEST_CUSTOMERS:
    try:
        result = client.table('customers').upsert(customer).execute()
        if result.data:
            customer_id = result.data[0]['id']
            _RUNTIME_IDS['customers'][customer['external_customer_id']] = customer_id
            print(f'Inserted customer: {customer["external_customer_id"]} -> {customer_id}')
    except Exception as e:
        print(f'Customer insert error: {e}')

print('Runtime IDs customers:', _RUNTIME_IDS['customers'])

# Insert orders
for order in TEST_ORDERS:
    try:
        customer_id = _RUNTIME_IDS['customers'].get(order.get('external_customer_id'))
        if not customer_id:
            customer_id = client.table('customers').select('id').eq('external_customer_id', order['external_customer_id']).single().execute()
            if customer_id.data:
                customer_id = customer_id.data['id']
            else:
                print(f'Customer not found for order {order["order_number"]}: {order["external_customer_id"]}')
                continue
        print(f'Customer ID for {order["external_customer_id"]}: {customer_id}')
        
        order_data = {k: v for k, v in order.items() if k != 'external_customer_id'}
        order_data['customer_id'] = customer_id
        print(f'Order data: {order_data}')
        
        result = client.table('orders').upsert(order_data).execute()
        if result.data:
            order_id = result.data[0]['id']
            _RUNTIME_IDS['orders'][order['order_number']] = order_id
            print(f'Inserted order: {order["order_number"]} -> {order_id}')
    except Exception as e:
        print(f'Order insert error: {e}')