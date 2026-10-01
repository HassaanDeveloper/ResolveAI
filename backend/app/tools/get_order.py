from typing import Optional
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import OrderResponse, ToolResult
from app.reliability import with_retry, DEFAULT_READ_RETRY, supabase_circuit_breaker


class GetOrderInput(ToolInput):
    order_id: str = Field(..., description="Order number (e.g., '10482')")


class GetOrderOutput(ToolOutput):
    order: Optional[OrderResponse] = None
    error: Optional[str] = None


class GetOrderTool(BaseTool):
    name = "get_order"
    category = "read"
    description = "Retrieve order details by order number"
    input_schema = GetOrderInput
    output_schema = GetOrderOutput

    async def execute(self, input_data: GetOrderInput) -> ToolResult:
        from app.services.database import get_supabase_client
        
        async def _get_order():
            supabase = get_supabase_client()
            
            # Use circuit breaker for Supabase calls
            async def _query():
                return supabase.table("orders").select(
                    "id, order_number, customer_id, status, total_amount, currency, created_at, updated_at"
                ).eq("order_number", input_data.order_id).single().execute()
            
            response = await supabase_circuit_breaker.call(_query)
            
            if not response.data:
                return self.error_result("NOT_FOUND", f"Order {input_data.order_id} not found")

            # Get customer name
            customer_response = supabase.table("customers").select("name").eq("id", response.data["customer_id"]).single().execute()
            customer_name = customer_response.data.get("name", "Unknown") if customer_response.data else "Unknown"

            order_data = OrderResponse(
                id=response.data["id"],
                order_number=response.data["order_number"],
                customer_id=response.data["customer_id"],
                customer_name=customer_name,
                status=response.data["status"],
                total_amount=response.data["total_amount"],
                currency=response.data["currency"],
                created_at=response.data["created_at"],
                updated_at=response.data["updated_at"]
            )
            return self.success_result(GetOrderOutput(order=order_data))
        
        # Execute with retry and handle retries exhausted
        try:
            return await with_retry(_get_order, policy=DEFAULT_READ_RETRY, operation_name="get_order")
        except Exception as e:
            return self.error_result("EXECUTION_ERROR", f"Failed to retrieve order after retries: {str(e)}")


get_order_tool = GetOrderTool()