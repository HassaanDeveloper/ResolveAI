from typing import Optional
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import CancellationResult, ToolResult
from app.reliability import idempotency_service


class CancelOrderInput(ToolInput):
    order_id: str = Field(..., description="Order number (e.g., '10482')")
    operation_id: str = Field(..., description="Idempotency key (e.g., 'cancel-order-10482')")
    reason: str = Field(default="Customer requested cancellation", description="Reason for cancellation")


class CancelOrderOutput(ToolOutput):
    result: Optional[CancellationResult] = None
    error: Optional[str] = None


class CancelOrderTool(BaseTool):
    name = "cancel_order"
    category = "side_effect"
    description = "Cancel an order (may require approval if already shipped)"
    requires_approval = True
    input_schema = CancelOrderInput
    output_schema = CancelOrderOutput

    async def execute(self, input_data: CancelOrderInput) -> ToolResult:
        from app.services.database import get_supabase_client
        
        try:
            # Check idempotency using the new service
            existing_result = await idempotency_service.check_idempotency(input_data.operation_id)
            if existing_result:
                if existing_result.idempotent and existing_result.success:
                    result_data = existing_result.data or {}
                    return self.success_result(CancelOrderOutput(result=CancellationResult(
                        success=True,
                        order_id=result_data.get("order_id"),
                        order_number=result_data.get("order_number"),
                        operation_id=input_data.operation_id,
                        status="duplicate",
                        message="Cancellation already processed (idempotent)",
                        requires_approval=result_data.get("requires_approval", False)
                    )))
                elif existing_result.idempotent and not existing_result.success:
                    return self.error_result("CONFLICT", f"Operation {input_data.operation_id} previously failed: {existing_result.error}")
                else:
                    return self.error_result("CONFLICT", f"Operation {input_data.operation_id} is already in progress")

            # Reserve the operation
            reserved = await idempotency_service.reserve_operation(input_data.operation_id, "cancel_order")
            if not reserved:
                return self.error_result("CONFLICT", f"Operation {input_data.operation_id} already exists")

            supabase = get_supabase_client()
            
            try:
                # Get order
                order_response = supabase.table("orders").select("id, order_number, status").eq("order_number", input_data.order_id).single().execute()
                
                if not order_response.data:
                    await idempotency_service.mark_failed(input_data.operation_id, f"Order {input_data.order_id} not found")
                    return self.error_result("NOT_FOUND", f"Order {input_data.order_id} not found")

                order = order_response.data
                
                # Check if already cancelled or refunded
                if order["status"] in ["cancelled", "refunded"]:
                    await idempotency_service.mark_failed(input_data.operation_id, f"Order already {order['status']}")
                    return self.error_result("VALIDATION_ERROR", f"Order already {order['status']}")

                # Check shipment status
                shipment_response = supabase.table("shipments").select("status").eq("order_id", order["id"]).execute()
                shipment_status = shipment_response.data[0]["status"] if shipment_response.data else None
                
                requires_approval = False
                if shipment_status in ["shipped", "in_transit", "delivered"]:
                    requires_approval = True

                # If already delivered, cannot cancel - would need return process
                if shipment_status == "delivered":
                    await idempotency_service.mark_failed(input_data.operation_id, "Cannot cancel delivered order")
                    return self.error_result("VALIDATION_ERROR", "Cannot cancel delivered order. Use return process instead.")

                # Mark as executing
                await idempotency_service.mark_executing(input_data.operation_id)

                # Update order status to cancelled
                supabase.table("orders").update({"status": "cancelled"}).eq("id", order["id"]).execute()

                # Update operation as executed
                result_data = {
                    "order_id": order["id"],
                    "order_number": order["order_number"],
                    "requires_approval": requires_approval
                }
                await idempotency_service.mark_executed(input_data.operation_id, result_data)

                message = "Order cancelled successfully"
                if requires_approval:
                    message += " (requires approval for shipped orders)"

                return self.success_result(CancelOrderOutput(result=CancellationResult(
                    success=True,
                    order_id=order["id"],
                    order_number=order["order_number"],
                    operation_id=input_data.operation_id,
                    status="cancelled",
                    message=message,
                    requires_approval=requires_approval
                )))

            except Exception as e:
                await idempotency_service.mark_failed(input_data.operation_id, str(e))
                return self.error_result("EXECUTION_ERROR", f"Failed to cancel order: {str(e)}")

        except Exception as e:
            # Try to mark operation as failed
            try:
                await idempotency_service.mark_failed(input_data.operation_id, str(e))
            except:
                pass
            return self.error_result("EXECUTION_ERROR", f"Failed to cancel order: {str(e)}")


cancel_order_tool = CancelOrderTool()