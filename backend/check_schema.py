from app.services.database import get_supabase_client
client = get_supabase_client()

# Query information_schema
result = client.rpc('exec_sql', {"sql": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'resolutions' ORDER BY ordinal_position"}).execute()
print('resolutions columns:')
for row in result.data:
    print(f'  {row}')

result = client.rpc('exec_sql', {"sql": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position"}).execute()
print('documents columns:')
for row in result.data:
    print(f'  {row}')