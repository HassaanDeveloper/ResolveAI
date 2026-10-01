import asyncio
import traceback
import sys
from evaluation.integration.real_runner import RealIntegrationRunner
from evaluation.integration.scenarios import real_scenario_store
from app.workflows.engine import workflow_engine
from app.workflows.models import ResolutionRequest

async def debug_tool001():
    runner = RealIntegrationRunner()
    
    print("Setting up test data...")
    await runner.setup_test_data()
    print("[OK] Test data seeded")
    
    doc_ids = await runner.seed_test_documents()
    print(f"[OK] Seeded {len(doc_ids)} test documents")
    
    # Run pre-scenario cleanup like real_runner does
    print("Running pre-scenario cleanup...")
    await runner.cleanup_test_data(full=False)
    print("[OK] Pre-scenario cleanup complete")
    
    # Get tool_001 scenario
    scenario = real_scenario_store.get_by_id("tool_001")
    if not scenario:
        print("Scenario tool_001 not found!")
        return
    
    print(f"\nRunning: {scenario.name} ({scenario.id})")
    print(f"Request ID: {scenario.input.request_id}")
    print(f"User Request: {scenario.input.user_request}")
    print(f"Customer ID: {scenario.input.customer_id}")
    print(f"Order ID: {scenario.input.order_id}")
    print()
    
    # Generate unique request_id (same as real_runner does)
    import time
    import uuid
    unique_suffix = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    original_request_id = scenario.input.request_id
    unique_request_id = f"{original_request_id}_{unique_suffix}"
    
    print(f"Unique Request ID: {unique_request_id}")
    
    resolution_request = ResolutionRequest(
        request_id=unique_request_id,
        user_request=scenario.input.user_request,
        customer_id=scenario.input.customer_id,
        order_id=scenario.input.order_id,
    )
    
    print("\n=== EXECUTING WORKFLOW ===")
    try:
        workflow = await workflow_engine.execute(resolution_request)
        
        print(f"\n=== WORKFLOW RESULT ===")
        print(f"  Status: {workflow.status}")
        print(f"  Intent: {workflow.intent}")
        print(f"  Errors: {workflow.errors}")
        print(f"  Tool Calls: {len(workflow.tool_calls)}")
        for tc in workflow.tool_calls:
            print(f"    - {tc.tool_name}: success={tc.success}, error={tc.error}")
            if tc.output_data:
                print(f"      output: {tc.output_data}")
        print(f"  Policy Result: {workflow.policy_result}")
        if workflow.policy_result:
            print(f"    decision: {workflow.policy_result.decision}")
            print(f"    reason: {workflow.policy_result.reason}")
        print(f"  Retrieved Docs: {len(workflow.retrieved_documents) if workflow.retrieved_documents else 0}")
        if workflow.retrieved_documents:
            for i, doc in enumerate(workflow.retrieved_documents):
                print(f"    [{i}] {doc}")
        
    except Exception as e:
        print(f"\n=== EXCEPTION CAUGHT ===")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")
        print(f"\n=== FULL TRACEBACK ===")
        traceback.print_exc()
    
    # Check operations table
    from app.services.database import get_supabase_client
    client = get_supabase_client()
    result = client.table("operations").select("*").execute()
    print(f"\n=== OPERATIONS TABLE ===")
    for op in result.data:
        print(f"  {op['operation_id']} | {op['operation_type']} | {op['status']}")
    
    # Check refunds table
    refunds = client.table("refunds").select("*").execute()
    print(f"\n=== REFUNDS TABLE ===")
    for r in refunds.data:
        print(f"  {r['id']} | {r['order_id']} | {r['amount']} | {r['status']} | {r['operation_id']}")
    
    # Cleanup
    print("\nCleaning up...")
    await runner.cleanup_test_documents(doc_ids)
    await runner.cleanup_test_data(full=True)
    print("[OK] Cleanup complete")

if __name__ == "__main__":
    asyncio.run(debug_tool001())