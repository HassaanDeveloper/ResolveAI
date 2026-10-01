from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import RefundCalculation, PolicySearchResult, ToolResult
from app.reliability import with_retry, DEFAULT_READ_RETRY, supabase_circuit_breaker, gemini_circuit_breaker


class CalculateRefundInput(ToolInput):
    order_id: str = Field(..., description="Order number (e.g., '10482')")


class CalculateRefundOutput(ToolOutput):
    calculation: Optional[RefundCalculation] = None
    error: Optional[str] = None


class CalculateRefundTool(BaseTool):
    name = "calculate_refund"
    category = "read"
    description = "Calculate eligible refund amount for an order based on policy"
    input_schema = CalculateRefundInput
    output_schema = CalculateRefundOutput

    async def execute(self, input_data: CalculateRefundInput) -> ToolResult:
        async def _calculate():
            from app.services.database import get_supabase_client
            from app.tools.search_company_policy import search_company_policy_tool, SearchCompanyPolicyInput
            
            supabase = get_supabase_client()
            
            # Get order details
            async def _get_order():
                return supabase.table("orders").select(
                    "id, order_number, customer_id, status, total_amount, currency"
                ).eq("order_number", input_data.order_id).single().execute()
            
            order_response = await supabase_circuit_breaker.call(_get_order)

            if not order_response.data:
                return self.error_result("NOT_FOUND", f"Order {input_data.order_id} not found")

            order = order_response.data
            
            # Get shipment status
            async def _get_shipment():
                return supabase.table("shipments").select("status, estimated_delivery_date, delivered_at").eq("order_id", order["id"]).execute()
            
            shipment_response = await supabase_circuit_breaker.call(_get_shipment)
            shipment_status = shipment_response.data[0]["status"] if shipment_response.data else None
            estimated_delivery = shipment_response.data[0].get("estimated_delivery_date") if shipment_response.data else None
            delivered_at = shipment_response.data[0].get("delivered_at") if shipment_response.data else None

            # Get existing refunds for this order
            async def _get_refunds():
                return supabase.table("refunds").select("amount, status").eq("order_id", order["id"]).execute()
            
            refund_response = await supabase_circuit_breaker.call(_get_refunds)
            existing_refunds = sum(r["amount"] for r in refund_response.data if r["status"] == "completed") if refund_response.data else 0

            # Determine eligibility
            eligible_amount = Decimal("0")
            eligibility_reason = ""
            policy_refs = []

            # Search for relevant policies (uses Gemini for embeddings)
            async def _search_policy():
                return await search_company_policy_tool.execute(SearchCompanyPolicyInput(
                    query=f"refund eligibility {order['status']} {shipment_status}",
                    max_results=3
                ))
            
            policy_search = await gemini_circuit_breaker.call(_search_policy)
            if policy_search.success and policy_search.data:
                for r in policy_search.data.get("results", []):
                    policy_refs.append(PolicySearchResult(**r))

            # Business logic for refund calculation
            if order["status"] == "refunded":
                eligibility_reason = "Order already fully refunded"
                eligible_amount = Decimal("0")
            elif order["status"] == "cancelled":
                eligibility_reason = "Order was cancelled, no refund needed"
                eligible_amount = Decimal("0")
            elif order["status"] == "delivered":
                # Check if within 30 days
                from datetime import datetime, timezone
                if delivered_at:
                    delivered_dt = datetime.fromisoformat(delivered_at.replace('Z', '+00:00'))
                    days_since = (datetime.now(timezone.utc) - delivered_dt).days
                    if days_since <= 30:
                        eligible_amount = Decimal(str(order["total_amount"])) - Decimal(str(existing_refunds))
                        eligibility_reason = f"Delivered {days_since} days ago, within 30-day policy"
                    else:
                        eligible_amount = Decimal("0")
                        eligibility_reason = f"Delivered {days_since} days ago, outside 30-day policy"
                else:
                    eligible_amount = Decimal("0")
                    eligibility_reason = "Delivered but no delivery timestamp"
            elif order["status"] == "shipped":
                if shipment_status == "delayed":
                    # Check if delayed beyond estimated delivery
                    from datetime import datetime, timezone
                    if estimated_delivery:
                        est_date = datetime.fromisoformat(estimated_delivery + "T23:59:59+00:00")
                        days_delayed = (datetime.now(timezone.utc) - est_date).days
                        if days_delayed >= 7:
                            eligible_amount = Decimal(str(order["total_amount"])) - Decimal(str(existing_refunds))
                            eligibility_reason = f"Shipment delayed {days_delayed} days beyond estimated delivery"
                        else:
                            eligible_amount = Decimal("0")
                            eligibility_reason = f"Shipment delayed only {days_delayed} days (need 7+)"
                    else:
                        eligible_amount = Decimal("0")
                        eligibility_reason = "No estimated delivery date"
                elif shipment_status == "failed":
                    eligible_amount = Decimal(str(order["total_amount"])) - Decimal(str(existing_refunds))
                    eligibility_reason = "Shipment failed"
                else:
                    eligible_amount = Decimal("0")
                    eligibility_reason = f"Shipped ({shipment_status}), not eligible for refund unless delayed/failed"
            elif order["status"] in ["pending", "processing"]:
                eligible_amount = Decimal("0")
                eligibility_reason = f"Order status is {order['status']}, not yet shipped"
            else:
                eligible_amount = Decimal("0")
                eligibility_reason = f"Unknown order status: {order['status']}"

            calculation = RefundCalculation(
                order_id=order["id"],
                order_number=order["order_number"],
                eligible_amount=eligible_amount,
                currency=order["currency"],
                eligibility_reason=eligibility_reason,
                policy_references=policy_refs
            )
            return self.success_result(CalculateRefundOutput(calculation=calculation))
        
        # Execute with retry
        return await with_retry(_calculate, policy=DEFAULT_READ_RETRY, operation_name="calculate_refund")


calculate_refund_tool = CalculateRefundTool()