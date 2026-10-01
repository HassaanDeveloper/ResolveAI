from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import EscalationResult, ToolResult


class CreateEscalationInput(ToolInput):
    reason: str = Field(..., description="Reason for escalation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context (order_id, customer_id, etc.)")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class CreateEscalationOutput(ToolOutput):
    result: Optional[EscalationResult] = None
    error: Optional[str] = None


class CreateEscalationTool(BaseTool):
    name = "create_escalation"
    category = "side_effect"
    description = "Create an escalation to human operator for complex cases"
    requires_approval = False  # Escalations don't need approval - they ARE the approval path
    input_schema = CreateEscalationInput
    output_schema = CreateEscalationOutput

    async def execute(self, input_data: CreateEscalationInput) -> ToolResult:
        from app.services.database import get_supabase_client
        import uuid
        from datetime import datetime, timezone
        
        try:
            supabase = get_supabase_client()
            
            escalation_id = f"esc-{uuid.uuid4().hex[:12]}"
            created_at = datetime.now(timezone.utc)

            # Store escalation in audit_events as a structured record
            # (In future, could have dedicated escalations table)
            event_data = {
                "escalation_id": escalation_id,
                "reason": input_data.reason,
                "context": input_data.context,
                "priority": input_data.priority,
                "status": "open"
            }
            
            supabase.table("audit_events").insert({
                "request_id": input_data.context.get("request_id", "unknown"),
                "resolution_id": input_data.context.get("resolution_id"),
                "event_type": "escalation_created",
                "event_data": event_data
            }).execute()

            return self.success_result(CreateEscalationOutput(result=EscalationResult(
                success=True,
                escalation_id=escalation_id,
                reason=input_data.reason,
                status="open",
                message="Escalation created and assigned to human operator queue",
                created_at=created_at
            )))

        except Exception as e:
            return self.error_result("EXECUTION_ERROR", f"Failed to create escalation: {str(e)}")


create_escalation_tool = CreateEscalationTool()