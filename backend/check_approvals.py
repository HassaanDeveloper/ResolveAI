import asyncio
from app.services.database import get_supabase_client

async def check_approvals():
    client = get_supabase_client()
    result = client.table('approval_requests').select('*').execute()
    print(f'Approvals ({len(result.data)}):')
    for a in result.data:
        print(f'  {a["id"]} | {a["action_type"]} | {a["status"]} | {a.get("policy_rule")} | {a.get("risk_level")} | {a.get("decision_reason")}')

asyncio.run(check_approvals())