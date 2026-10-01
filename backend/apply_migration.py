from app.services.database import get_supabase_client

client = get_supabase_client()

# Check current enum values
result = client.rpc('exec_sql', {'sql': "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'operation_status'::regtype ORDER BY enumsortorder;"}).execute()
print("Current enum values:")
for row in result.data:
    print(f"  {row['enumlabel']}")

# Add executing
try:
    result = client.rpc('exec_sql', {'sql': "ALTER TYPE operation_status ADD VALUE 'executing';"}).execute()
    print("Added 'executing' successfully")
except Exception as e:
    print(f"Error adding executing: {e}")

# Verify
result = client.rpc('exec_sql', {'sql': "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'operation_status'::regtype ORDER BY enumsortorder;"}).execute()
print("\nUpdated enum values:")
for row in result.data:
    print(f"  {row['enumlabel']}")