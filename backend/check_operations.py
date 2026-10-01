import asyncio
from app.services.database import get_supabase_client

async def check_operations():
    client = get_supabase_client()
    
    # Check all operations
    result = client.table("operations").select("*").execute()
    print("All operations:")
    for op in result.data:
        print(f"  {op['operation_id']} | {op['operation_type']} | {op['status']}")

if __name__ == "__main__":
    asyncio.run(check_operations())