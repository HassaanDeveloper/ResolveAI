from typing import Optional
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import ShipmentResponse, ToolResult
from app.reliability import with_retry, DEFAULT_READ_RETRY, supabase_circuit_breaker


class GetShippingStatusInput(ToolInput):
    order_id: str = Field(..., description="Order number (e.g., '10482')")


class GetShippingStatusOutput(ToolOutput):
    shipment: Optional[ShipmentResponse] = None
    error: Optional[str] = None


class GetShippingStatusTool(BaseTool):
    name = "get_shipping_status"
    category = "read"
    description = "Retrieve shipment tracking information for an order"
    input_schema = GetShippingStatusInput
    output_schema = GetShippingStatusOutput

    async def execute(self, input_data: GetShippingStatusInput) -> ToolResult:
        from app.services.database import get_supabase_client
        
        async def _get_shipping():
            supabase = get_supabase_client()
            
            async def _get_order():
                return supabase.table("orders").select("id").eq("order_number", input_data.order_id).single().execute()
            
            order_response = await supabase_circuit_breaker.call(_get_order)
            
            if not order_response.data:
                return self.error_result("NOT_FOUND", f"Order {input_data.order_id} not found")

            order_uuid = order_response.data["id"]
            
            async def _get_shipment():
                return supabase.table("shipments").select(
                    "id, order_id, carrier, tracking_number, status, estimated_delivery_date, delivered_at, updated_at"
                ).eq("order_id", order_uuid).execute()
            
            shipment_response = await supabase_circuit_breaker.call(_get_shipment)

            if not shipment_response.data or len(shipment_response.data) == 0:
                return self.error_result("NOT_FOUND", f"No shipment found for order {input_data.order_id}")

            # Use the most recent shipment
            shipment = shipment_response.data[0]
            
            shipment_data = ShipmentResponse(
                id=shipment["id"],
                order_id=shipment["order_id"],
                carrier=shipment["carrier"],
                tracking_number=shipment["tracking_number"],
                status=shipment["status"],
                estimated_delivery_date=shipment.get("estimated_delivery_date"),
                delivered_at=shipment.get("delivered_at"),
                updated_at=shipment["updated_at"]
            )
            return self.success_result(GetShippingStatusOutput(shipment=shipment_data))
        
        # Execute with retry
        return await with_retry(_get_shipping, policy=DEFAULT_READ_RETRY, operation_name="get_shipping_status")


get_shipping_status_tool = GetShippingStatusTool()