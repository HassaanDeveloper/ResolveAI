from typing import Optional
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import CustomerResponse, ToolResult
from app.reliability import with_retry, DEFAULT_READ_RETRY, supabase_circuit_breaker


class GetCustomerInput(ToolInput):
    customer_id: str = Field(..., description="Customer external ID (e.g., 'CUST-001')")


class GetCustomerOutput(ToolOutput):
    customer: Optional[CustomerResponse] = None
    error: Optional[str] = None


class GetCustomerTool(BaseTool):
    name = "get_customer"
    category = "read"
    description = "Retrieve customer details by external customer ID"
    input_schema = GetCustomerInput
    output_schema = GetCustomerOutput

    async def execute(self, input_data: GetCustomerInput) -> ToolResult:
        from app.services.database import get_supabase_client
        
        async def _get_customer():
            supabase = get_supabase_client()
            
            async def _query():
                return supabase.table("customers").select(
                    "id, external_customer_id, name, email, account_status, created_at"
                ).eq("external_customer_id", input_data.customer_id).single().execute()
            
            response = await supabase_circuit_breaker.call(_query)
            
            if not response.data:
                return self.error_result("NOT_FOUND", f"Customer {input_data.customer_id} not found")

            customer_data = CustomerResponse(
                id=response.data["id"],
                external_customer_id=response.data["external_customer_id"],
                name=response.data["name"],
                email=response.data["email"],
                account_status=response.data["account_status"],
                created_at=response.data["created_at"]
            )
            return self.success_result(GetCustomerOutput(customer=customer_data))
        
        # Execute with retry
        return await with_retry(_get_customer, policy=DEFAULT_READ_RETRY, operation_name="get_customer")


get_customer_tool = GetCustomerTool()