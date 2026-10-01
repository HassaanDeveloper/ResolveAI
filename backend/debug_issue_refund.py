import asyncio
from decimal import Decimal
from app.services.database import get_supabase_client
from evaluation.integration.real_runner import RealIntegrationRunner
from evaluation.integration.scenarios import real_scenario_store
from app.workflows.engine import workflow_engine
from app.workflows.models import ResolutionRequest
import time
import uuid
import traceback

# Monkey-patch the issue_refund tool to add detailed tracing at each step
from app.tools import issue_refund as issue_refund_module
original_execute = issue_refund_module.IssueRefundTool.execute

async def traced_execute(self, input_data):
    print(f"\n=== ISSUE_REFUND TRACE ===")
    print(f"Input: order_id={input_data.order_id}, amount={input_data.amount}, operation_id={input_data.operation_id}")
    supabase = get_supabase_client()
    
    try:
        # Check idempotency
        from app.reliability import idempotency_service
        existing_result = await idempotency_service.check_idempotency(input_data.operation_id)
        print(f"Idempotency check: {existing_result}")
        
        # Reserve
        reserved = await idempotency_service.reserve_operation(input_data.operation_id, "issue_refund")
        print(f"Reserved: {reserved}")
        
        # Get order
        order_response = supabase.table("orders").select("id, order_number, total_amount, currency").eq("order_number", input_data.order_id).single().execute()
        print(f"Order lookup: {order_response.data}")
        
        if not order_response.data:
            print("Order not found!")
            return None
            
        order = order_response.data
        
        # Validate amount
        if input_data.amount > Decimal(str(order["total_amount"])):
            print("Amount exceeds order total")
            return None
            
        # Check existing refunds
        refund_response = supabase.table("refunds").select("amount, status").eq("order_id", order["id"]).execute()
        print(f"Existing refunds for order: {refund_response.data}")
        existing_refunds = sum(Decimal(str(r["amount"])) for r in refund_response.data if r["status"] == "completed") if refund_response.data else Decimal("0")
        print(f"Existing completed refunds total: {existing_refunds}")
        
        if existing_refunds + input_data.amount > Decimal(str(order["total_amount"])):
            print("Total would exceed order amount")
            return None
            
        # Mark executing
        await idempotency_service.mark_executing(input_data.operation_id)
        print("Marked executing")
        
        # Create refund record
        refund_data = {
            "order_id": order["id"],
            "amount": float(input_data.amount),
            "currency": order["currency"],
            "status": "processing",
            "operation_id": input_data.operation_id
        }
        print(f"Inserting refund: {refund_data}")
        
        refund_response = supabase.table("refunds").insert(refund_data).execute()
        print(f"INSERT response: {refund_response.data}")
        print(f"INSERT response count: {len(refund_response.data) if refund_response.data else 0}")
        
        if not refund_response.data:
            print("INSERT returned no data!")
            return None
            
        refund_id = refund_response.data[0]["id"]
        print(f"Created refund ID: {refund_id}")
        
        # Update to completed
        from datetime import datetime, timezone
        processed_at = datetime.now(timezone.utc)
        
        update_data = {
            "status": "completed",
            "processed_at": processed_at.isoformat()
        }
        print(f"Updating refund {refund_id} with: {update_data}")
        
        update_response = supabase.table("refunds").update(update_data).eq("id", refund_id).execute()
        print(f"UPDATE response: {update_response.data}")
        print(f"UPDATE response count: {len(update_response.data) if update_response.data else 0}")
        
        # Mark executed
        result_data = {
            "refund_id": refund_id,
            "currency": order["currency"],
            "processed_at": processed_at.isoformat()
        }
        await idempotency_service.mark_executed(input_data.operation_id, result_data)
        print("Marked executed")
        
        return "SUCCESS"
        
    except Exception as e:
        print(f"EXCEPTION:")
        traceback.print_exc()
        raise

issue_refund_module.IssueRefundTool.execute = traced_execute

async def debug_issue_refund():
    """Test the exact issue_refund flow within the workflow context"""
    runner = RealIntegrationRunner()
    
    print("Setting up test data...")
    await runner.setup_test_data()
    print("[OK] Test data seeded")
    
    doc_ids = await runner.seed_test_documents()
    print(f"[OK] Seeded {len(doc_ids)} test documents")
    
    # Get tool_001 scenario
    scenario = real_scenario_store.get_by_id("tool_001")
    
    # Generate unique request_id
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
    workflow = await workflow_engine.execute(resolution_request)
    
    print(f"\n=== WORKFLOW RESULT ===")
    print(f"  Status: {workflow.status}")
    print(f"  Intent: {workflow.intent}")
    print(f"  Errors: {workflow.errors}")
    
    # Now check the refunds table
    supabase = get_supabase_client()
    refunds = supabase.table("refunds").select("*").execute()
    print(f"\n=== REFUNDS TABLE ===")
    print(f"Refunds: {refunds.data}")
    
    # Cleanup
    print("\nCleaning up...")
    await runner.cleanup_test_documents(doc_ids)
    await runner.cleanup_test_data(full=True)
    print("[OK] Cleanup complete")

if __name__ == "__main__":
    asyncio.run(debug_issue_refund())