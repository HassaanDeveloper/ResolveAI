import re
import uuid
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from app.workflows.models import (
    ResolutionWorkflow,
    ResolutionRequest,
    ResolutionResponse,
    WorkflowStepResult,
    WorkflowStatus,
    WorkflowIntent,
    ToolCallRecord,
    PolicyCheckRecord,
    ApprovalRecord,
    VerificationRecord,
)
from app.tools import tool_registry
from app.policies import policy_engine, PolicyInput, PolicyDecision, ActionType
from app.approvals import approval_service, ApprovalCreate, ApprovalActionType, ApprovalStatus
from app.audit import audit_service, AuditEventType
from app.services.database import get_supabase_client


class WorkflowEngine:
    """
    Deterministic workflow engine for business resolution.

    Implements the state machine:
    REQUEST → UNDERSTAND → INVESTIGATE → RETRIEVE POLICY → DECIDE → 
    POLICY CHECK → APPROVAL IF REQUIRED → EXECUTE → VERIFY → AUDIT → RESPOND
    """

    # Order ID pattern (e.g., 10482, 10521, etc.)
    ORDER_ID_PATTERN = re.compile(r'\b(\d{5})\b')

    def __init__(self):
        pass

    async def _resolve_business_keys(self, workflow: ResolutionWorkflow) -> None:
        """Resolve business keys (eval-test-*) to actual UUIDs from the database."""
        client = get_supabase_client()
        
        # Resolve customer_id if it's a business key
        if workflow.customer_id and workflow.customer_id.startswith("eval-test-"):
            result = client.table("customers").select("id").eq("external_customer_id", workflow.customer_id).single().execute()
            if result.data:
                workflow.customer_id = result.data["id"]
        
        # Keep order_id as business key (order_number) for tool compatibility
        # The order_number field stores the business key for display
        if workflow.order_id and workflow.order_id.startswith("eval-test-"):
            workflow.order_number = workflow.order_id
    
    async def _get_order_uuid(self, order_number: str) -> Optional[str]:
        """Get the UUID for an order by its business key (order_number)."""
        client = get_supabase_client()
        result = client.table("orders").select("id").eq("order_number", order_number).limit(1).execute()
        if result.data:
            return result.data[0]["id"]
        return None

    async def _get_customer_uuid(self, customer_key: str) -> Optional[str]:
        """Get the UUID for a customer by its business key (external_customer_id)."""
        client = get_supabase_client()
        result = client.table("customers").select("id").eq("external_customer_id", customer_key).limit(1).execute()
        if result.data:
            return result.data[0]["id"]
        return None

    @staticmethod
    def _is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except (ValueError, TypeError):
            return False

    async def _persist_workflow(self, workflow: ResolutionWorkflow) -> None:
        """Persist workflow state to the resolutions table."""
        client = get_supabase_client()
        
        # Resolve business keys to UUIDs for database persistence
        customer_uuid = None
        if workflow.customer_id:
            customer_uuid = (
                workflow.customer_id
                if self._is_uuid(workflow.customer_id)
                else await self._get_customer_uuid(workflow.customer_id)
            )

        order_uuid = None
        if workflow.order_number:
            order_uuid = await self._get_order_uuid(workflow.order_number)
        
        # Helper to convert datetime and Decimal objects to ISO format strings for JSON serialization
        def serialize_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, Decimal):
                return str(value)
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            else:
                return value
        
        # Serialize tool_calls and other datetime fields
        serialized_tool_calls = []
        for call in workflow.tool_calls:
            call_dict = call.model_dump()
            call_dict = serialize_value(call_dict)
            serialized_tool_calls.append(call_dict)
        
        serialized_retrieved_documents = serialize_value(workflow.retrieved_documents)
        serialized_policy_result = serialize_value(workflow.policy_result.model_dump()) if workflow.policy_result else None
        serialized_approval = serialize_value(workflow.approval.model_dump()) if workflow.approval else None
        serialized_action_result = serialize_value(workflow.action_result)
        serialized_verification = serialize_value(workflow.verification.model_dump()) if workflow.verification else None
        serialized_errors = workflow.errors
        serialized_context = serialize_value(workflow.context)
        
        data = {
            "id": workflow.id,
            "request_id": workflow.request_id,
            "user_request": workflow.user_request,
            "intent": workflow.intent.value if workflow.intent else None,
            "status": workflow.status.value,
            "customer_id": customer_uuid,
            "order_id": order_uuid,
            "order_number": workflow.order_number,
            "retrieved_documents": serialized_retrieved_documents,
            "tool_calls": serialized_tool_calls,
            "policy_result": serialized_policy_result,
            "approval": serialized_approval,
            "action_result": serialized_action_result,
            "verification": serialized_verification,
            "final_status": workflow.final_status,
            "errors": serialized_errors,
            "context": serialized_context,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
        }
        client.table("resolutions").upsert(data, on_conflict="request_id").execute()

    def _extract_order_id(self, user_request: str) -> Optional[str]:
        """Extract order ID from user request using deterministic parsing."""
        matches = self.ORDER_ID_PATTERN.findall(user_request)
        if matches:
            # Return the first match
            return matches[0]
        return None

    def _classify_intent(self, user_request: str) -> WorkflowIntent:
        """Classify intent using keyword matching (deterministic, no LLM)."""
        request_lower = user_request.lower()

        if any(kw in request_lower for kw in ["refund", "money back", "return money"]):
            return WorkflowIntent.REFUND_REQUEST
        elif any(kw in request_lower for kw in ["cancel", "cancellation", "stop order"]):
            return WorkflowIntent.CANCELLATION_REQUEST
        elif any(kw in request_lower for kw in ["where is", "shipping", "delivery", "track", "arrived"]):
            return WorkflowIntent.SHIPPING_INQUIRY
        elif any(kw in request_lower for kw in ["escalate", "manager", "supervisor", "complaint"]):
            return WorkflowIntent.ESCALATION_REQUEST
        else:
            return WorkflowIntent.UNKNOWN

    async def _record_tool_call(
        self,
        workflow: ResolutionWorkflow,
        tool_name: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Record a tool call in the workflow."""
        workflow.tool_calls.append(ToolCallRecord(
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            success=success,
            error=error,
            timestamp=datetime.utcnow()
        ))
        workflow.updated_at = datetime.utcnow()

    async def execute(self, request: ResolutionRequest) -> ResolutionWorkflow:
        """
        Execute the full resolution workflow.

        This is the main entry point that runs all steps in sequence.
        """
        # Initialize workflow
        workflow = ResolutionWorkflow(
            request_id=request.request_id,
            user_request=request.user_request,
            customer_id=request.customer_id,
            order_id=request.order_id,
        )

        # Resolve business keys to UUIDs before any database operations
        await self._resolve_business_keys(workflow)

        # Persist initial workflow state FIRST (before any audit events)
        await self._persist_workflow(workflow)
        
        # Record initial request received
        await audit_service.record_event_simple(
            request_id=workflow.request_id,
            event_type=AuditEventType.REQUEST_RECEIVED,
            event_data={"user_request": workflow.user_request},
            resolution_id=workflow.id,
        )
        
        try:
            # Step 1: UNDERSTAND - Extract order ID and classify intent
            workflow = await self._step_understand(workflow)
            if workflow.status == WorkflowStatus.FAILED:
                return workflow

            # Step 2: INVESTIGATE - Retrieve order and shipping status
            workflow = await self._step_investigate(workflow)
            await self._persist_workflow(workflow)
            if workflow.status == WorkflowStatus.FAILED:
                return workflow

            # Step 3: RETRIEVE POLICY - Search for relevant policies
            workflow = await self._step_retrieve_policy(workflow)
            await self._persist_workflow(workflow)

            # Step 4: DECIDE - Calculate refund if applicable
            workflow = await self._step_decide(workflow)
            await self._persist_workflow(workflow)

            # Step 5: POLICY CHECK - Run deterministic policy engine
            workflow = await self._step_policy_check(workflow)
            await self._persist_workflow(workflow)
            if workflow.status in [WorkflowStatus.REJECTED, WorkflowStatus.FAILED]:
                return workflow

            # Step 6: APPROVAL IF REQUIRED
            workflow = await self._step_approval(workflow)
            await self._persist_workflow(workflow)
            if workflow.status == WorkflowStatus.PENDING_APPROVAL:
                return workflow  # Wait for human approval

            # Step 7: EXECUTE - Perform the action
            workflow = await self._step_execute(workflow)
            await self._persist_workflow(workflow)
            if workflow.status == WorkflowStatus.FAILED:
                return workflow

            # Step 8: VERIFY - Verify the action succeeded
            workflow = await self._step_verify(workflow)
            await self._persist_workflow(workflow)

            # Step 9: COMPLETE
            workflow = await self._step_complete(workflow)
            await self._persist_workflow(workflow)

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(f"Workflow execution error: {str(e)}")
            workflow.updated_at = datetime.utcnow()
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.WORKFLOW_FAILED,
                event_data={"error": str(e)},
                resolution_id=workflow.id,
            )

        # Record final completion
        if workflow.status == WorkflowStatus.COMPLETED:
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.WORKFLOW_COMPLETED,
                event_data={"final_status": workflow.final_status},
                resolution_id=workflow.id,
            )

        return workflow

    async def _rehydrate_workflow(self, resolution_id: str) -> ResolutionWorkflow:
        """Rebuild a ResolutionWorkflow from its persisted `resolutions` row.

        Needed because a workflow that stopped at PENDING_APPROVAL is no longer
        in memory when a human decision arrives later.
        """
        client = get_supabase_client()
        result = (
            client.table("resolutions")
            .select("*")
            .eq("id", resolution_id)
            .single()
            .execute()
        )
        row = result.data

        tool_calls = [ToolCallRecord(**tc) for tc in (row.get("tool_calls") or [])]

        workflow = ResolutionWorkflow(
            id=row["id"],
            request_id=row["request_id"],
            user_request=row.get("user_request") or "",
            intent=WorkflowIntent(row["intent"]) if row.get("intent") else WorkflowIntent.UNKNOWN,
            status=WorkflowStatus(row["status"]) if row.get("status") else WorkflowStatus.PENDING,
            # The steps below address the order by its business key
            # (e.g. "10482"), matching the auto-approved path, whereas the
            # persisted `order_id` column holds the internal UUID.
            customer_id=row.get("customer_id"),
            order_id=row.get("order_number"),
            order_number=row.get("order_number"),
            retrieved_documents=row.get("retrieved_documents") or [],
            tool_calls=tool_calls,
            policy_result=PolicyCheckRecord(**row["policy_result"]) if row.get("policy_result") else None,
            approval=ApprovalRecord(**row["approval"]) if row.get("approval") else None,
            action_result=row.get("action_result"),
            verification=VerificationRecord(**row["verification"]) if row.get("verification") else None,
            final_status=row.get("final_status"),
            errors=row.get("errors") or [],
            context=row.get("context") or {},
        )
        return workflow

    async def resume_after_approval(self, resolution_id: str) -> Optional[ResolutionWorkflow]:
        """Resume a workflow that was parked at PENDING_APPROVAL.

        Runs the *existing* step chain (approval → execute → verify →
        mark-executed → complete) so the approved action is carried out by the
        same code the auto-approved path uses. No business logic is duplicated.
        """
        try:
            workflow = await self._rehydrate_workflow(resolution_id)
        except Exception as e:
            await audit_service.record_event_simple(
                request_id="unknown",
                event_type=AuditEventType.WORKFLOW_FAILED,
                event_data={"reason": "Failed to reload workflow for approval resume",
                            "error": str(e), "resolution_id": resolution_id},
                resolution_id=None,
            )
            return None

        try:
            # Step 6: re-read the human decision and move to EXECUTING.
            workflow = await self._step_approval(workflow)
            await self._persist_workflow(workflow)
            if workflow.status in (WorkflowStatus.PENDING_APPROVAL, WorkflowStatus.REJECTED,
                                   WorkflowStatus.FAILED):
                return workflow

            # Step 7: execute the authorized action.
            workflow = await self._step_execute(workflow)
            await self._persist_workflow(workflow)
            if workflow.status == WorkflowStatus.FAILED:
                await self._fail_pending_approval(workflow, workflow.errors[-1] if workflow.errors else "Execution failed")
                return workflow

            # Step 8: verify against real state.
            workflow = await self._step_verify(workflow)
            await self._persist_workflow(workflow)
            if workflow.status == WorkflowStatus.FAILED:
                await self._fail_pending_approval(workflow, workflow.verification.error if workflow.verification else "Verification failed")
                return workflow

            # Only now is the approval genuinely "executed".
            await self._step_mark_approval_executed(workflow)

            # Step 9: complete.
            workflow = await self._step_complete(workflow)
            await self._persist_workflow(workflow)
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(f"Approval resume error: {str(e)}")
            workflow.final_status = "failed"
            await self._persist_workflow(workflow)
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.WORKFLOW_FAILED,
                event_data={"reason": "Approval resume error", "error": str(e)},
                resolution_id=workflow.id,
            )

        return workflow

    async def _fail_pending_approval(self, workflow: ResolutionWorkflow, reason: str) -> None:
        """Move an approved-but-unsatisfied approval to `failed` honestly."""
        approval_id = workflow.context.get("approval_id")
        if not approval_id:
            return
        try:
            # Re-read the live row: the workflow snapshot was persisted before
            # the human decision, so it still says "pending".
            current = await approval_service.get_approval(approval_id)
            if current and current.status == ApprovalStatus.APPROVED:
                await approval_service.transition_to_failed(approval_id, reason)
        except Exception as e:
            workflow.errors.append(f"Warning: could not mark approval failed: {e}")
        workflow.final_status = "failed"
        await self._persist_workflow(workflow)

    async def _step_understand(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 1: UNDERSTAND - Extract order ID and classify intent."""
        workflow.status = WorkflowStatus.UNDERSTANDING

        # Extract order ID from user request if not provided
        if not workflow.order_id:
            extracted = self._extract_order_id(workflow.user_request)
            if extracted:
                workflow.order_id = extracted
                workflow.order_number = extracted

        # Classify intent
        workflow.intent = self._classify_intent(workflow.user_request)

        if workflow.intent == WorkflowIntent.UNKNOWN:
            workflow.errors.append("Could not determine request intent")
            # Continue anyway - might be able to infer from context

        workflow.status = WorkflowStatus.INVESTIGATING
        workflow.updated_at = datetime.utcnow()

        # Record intent identified
        await audit_service.record_event_simple(
            request_id=workflow.request_id,
            event_type=AuditEventType.INTENT_IDENTIFIED,
            event_data={"intent": workflow.intent.value},
            resolution_id=workflow.id,
        )
        return workflow

    async def _step_investigate(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 2: INVESTIGATE - Retrieve order and shipping status."""
        workflow.status = WorkflowStatus.INVESTIGATING

        if not workflow.order_id:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append("No order ID available for investigation")
            return workflow

        # Get order details
        order_result = await tool_registry.execute("get_order", {"order_id": workflow.order_id})
        await self._record_tool_call(
            workflow, "get_order", {"order_id": workflow.order_id},
            order_result.data if order_result.success else None,
            order_result.success, order_result.error.message if order_result.error else None
        )

        if not order_result.success:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(f"Failed to retrieve order: {order_result.error.message if order_result.error else 'Unknown error'}")
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.ORDER_RETRIEVED,
                event_data={"success": False, "order_id": workflow.order_id, "error": "Failed to retrieve"},
                resolution_id=workflow.id,
            )
            return workflow

        order_data = order_result.data["order"]
        workflow.order_number = order_data["order_number"]
        workflow.customer_id = order_data["customer_id"]

        # Record order retrieved
        await audit_service.record_event_simple(
            request_id=workflow.request_id,
            event_type=AuditEventType.ORDER_RETRIEVED,
            event_data={"order_number": workflow.order_number, "status": order_data["status"]},
            resolution_id=workflow.id,
        )

        # Get shipping status
        shipping_result = await tool_registry.execute("get_shipping_status", {"order_id": workflow.order_id})
        await self._record_tool_call(
            workflow, "get_shipping_status", {"order_id": workflow.order_id},
            shipping_result.data if shipping_result.success else None,
            shipping_result.success, shipping_result.error.message if shipping_result.error else None
        )

        if shipping_result.success:
            workflow.retrieved_documents.append({
                "type": "shipping_status",
                "data": shipping_result.data["shipment"]
            })

            # Record shipment checked
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.SHIPMENT_CHECKED,
                event_data={"shipment_status": shipping_result.data["shipment"]["status"]},
                resolution_id=workflow.id,
            )

        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _step_retrieve_policy(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 3: RETRIEVE POLICY - Search for relevant company policies."""
        workflow.status = WorkflowStatus.RETRIEVING_POLICY

        # Build search query based on intent and order status
        query_parts = [workflow.intent.value.replace("_", " ")]
        if workflow.order_id:
            # We'll get order status from tool calls
            for call in workflow.tool_calls:
                if call.tool_name == "get_order" and call.output_data:
                    query_parts.append(call.output_data.get("order", {}).get("status", ""))
                if call.tool_name == "get_shipping_status" and call.output_data:
                    query_parts.append(call.output_data.get("shipment", {}).get("status", ""))

        query = " ".join(filter(None, query_parts))

        policy_result = await tool_registry.execute("search_company_policy", {"query": query, "max_results": 5})
        await self._record_tool_call(
            workflow, "search_company_policy", {"query": query, "max_results": 5},
            policy_result.data if policy_result.success else None,
            policy_result.success, policy_result.error.message if policy_result.error else None
        )

        if policy_result.success:
            workflow.retrieved_documents.extend([
                {"type": "policy", "data": r} for r in policy_result.data.get("results", [])
            ])

            # Record policy retrieved
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.POLICY_RETRIEVED,
                event_data={"query": query, "results_count": len(policy_result.data.get("results", []))},
                resolution_id=workflow.id,
            )

        workflow.status = WorkflowStatus.INVESTIGATING
        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _step_decide(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 4: DECIDE - Calculate refund if this is a refund request."""
        workflow.status = WorkflowStatus.DECIDING

        if workflow.intent == WorkflowIntent.REFUND_REQUEST and workflow.order_id:
            refund_result = await tool_registry.execute("calculate_refund", {"order_id": workflow.order_id})
            await self._record_tool_call(
                workflow, "calculate_refund", {"order_id": workflow.order_id},
                refund_result.data if refund_result.success else None,
                refund_result.success, refund_result.error.message if refund_result.error else None
            )

            if refund_result.success and refund_result.data:
                workflow.retrieved_documents.append({
                    "type": "refund_calculation",
                    "data": refund_result.data["calculation"]
                })

                # Record refund calculated
                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.REFUND_CALCULATED,
                    event_data={"eligible_amount": str(refund_result.data.get("calculation", {}).get("eligible_amount", 0))},
                    resolution_id=workflow.id,
                )

        workflow.status = WorkflowStatus.POLICY_CHECK
        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _step_policy_check(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 5: POLICY CHECK - Run deterministic policy engine."""
        workflow.status = WorkflowStatus.POLICY_CHECK

        # Determine action type based on intent
        action_type_map = {
            WorkflowIntent.REFUND_REQUEST: ActionType.ISSUE_REFUND,
            WorkflowIntent.CANCELLATION_REQUEST: ActionType.CANCEL_ORDER,
            WorkflowIntent.ESCALATION_REQUEST: ActionType.CREATE_ESCALATION,
        }
        action_type = action_type_map.get(workflow.intent, ActionType.ISSUE_REFUND)

        # Gather facts for policy evaluation
        order_status = None
        shipment_status = None
        refund_amount = None
        eligibility_satisfied = False
        eligibility_reason = ""
        policy_evidence = []

        for call in workflow.tool_calls:
            if call.tool_name == "get_order" and call.output_data:
                order_status = call.output_data.get("order", {}).get("status")
            if call.tool_name == "get_shipping_status" and call.output_data:
                shipment_status = call.output_data.get("shipment", {}).get("status")
            if call.tool_name == "calculate_refund" and call.output_data:
                calc = call.output_data.get("calculation", {})
                refund_amount = Decimal(str(calc.get("eligible_amount", 0))) if calc.get("eligible_amount") else None
                eligibility_satisfied = calc.get("eligible_amount", 0) > 0
                eligibility_reason = calc.get("eligibility_reason", "")
                policy_evidence = calc.get("policy_references", [])

        policy_input = PolicyInput(
            action_type=action_type,
            order_status=order_status,
            shipment_status=shipment_status,
            refund_amount=refund_amount,
            eligibility_satisfied=eligibility_satisfied,
            eligibility_reason=eligibility_reason,
            policy_evidence=policy_evidence,
        )

        policy_output = policy_engine.evaluate(policy_input)
        workflow.policy_result = PolicyCheckRecord(
            action_type=action_type.value,
            decision=policy_output.decision.value,
            reason=policy_output.reason,
            policy_rule=policy_output.policy_rule,
            risk_level=policy_output.risk_level.value,
            approval_tier=policy_output.approval_tier,
            conditions=policy_output.conditions,
        )

        # Record policy evaluated
        await audit_service.record_event_simple(
            request_id=workflow.request_id,
            event_type=AuditEventType.POLICY_EVALUATED,
            event_data={
                "decision": policy_output.decision.value,
                "reason": policy_output.reason,
                "policy_rule": policy_output.policy_rule,
                "risk_level": policy_output.risk_level.value,
            },
            resolution_id=workflow.id,
        )

        # Handle policy decision
        if policy_output.decision == PolicyDecision.DENY:
            workflow.status = WorkflowStatus.REJECTED
            workflow.final_status = "rejected"
            workflow.errors.append(f"Policy denied: {policy_output.reason}")

            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.WORKFLOW_FAILED,
                event_data={"reason": "Policy denied", "reason": policy_output.reason},
                resolution_id=workflow.id,
            )
        elif policy_output.decision == PolicyDecision.REQUIRES_APPROVAL:
            workflow.status = WorkflowStatus.PENDING_APPROVAL
            # Create approval request in the approval system
            try:
                approval_request = ApprovalCreate(
                    resolution_id=workflow.id,
                    action_type=ApprovalActionType(action_type.value),
                    action_payload={
                        "order_id": workflow.order_id,
                        "amount": str(refund_amount) if refund_amount else None,
                    },
                    reason=policy_output.reason,
                    policy_rule=policy_output.policy_rule,
                    risk_level=policy_output.risk_level.value,
                )
                approval_response = await approval_service.create_approval(approval_request)
                workflow.approval = ApprovalRecord(
                    status="pending",
                    requested_at=datetime.utcnow(),
                    reason=policy_output.reason,
                )
                # Store the approval ID for later reference
                workflow.context["approval_id"] = approval_response.approval.id

                # Record approval requested
                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.APPROVAL_REQUESTED,
                    event_data={
                        "approval_id": approval_response.approval.id,
                        "reason": policy_output.reason,
                        "policy_rule": policy_output.policy_rule,
                        "risk_level": policy_output.risk_level.value,
                    },
                    resolution_id=workflow.id,
                )
            except Exception as e:
                workflow.status = WorkflowStatus.FAILED
                workflow.errors.append(f"Failed to create approval request: {str(e)}")
        else:  # ALLOW
            workflow.status = WorkflowStatus.EXECUTING

        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _step_approval(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 6: APPROVAL IF REQUIRED - Handle approval workflow."""
        if workflow.status != WorkflowStatus.PENDING_APPROVAL:
            return workflow

        # Check approval status from approval service
        approval_id = workflow.context.get("approval_id")
        if not approval_id:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append("No approval ID found in workflow context")
            return workflow

        try:
            approval = await approval_service.get_approval(approval_id)

            if approval.status == ApprovalStatus.APPROVED:
                # The approval is granted, but NOT yet executed. The status
                # transition to `executed` happens only after the action has
                # actually run and verified (see _step_mark_approval_executed).
                workflow.status = WorkflowStatus.EXECUTING

                # Record approval granted
                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.APPROVAL_GRANTED,
                    event_data={"approval_id": approval_id, "decided_by": approval.decided_by},
                    resolution_id=workflow.id,
                )
            elif approval.status == ApprovalStatus.REJECTED:
                workflow.status = WorkflowStatus.REJECTED
                workflow.final_status = "rejected"
                workflow.errors.append(f"Approval rejected: {approval.decision_reason or 'No reason provided'}")

                # Record approval rejected
                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.APPROVAL_REJECTED,
                    event_data={"approval_id": approval_id, "reason": approval.decision_reason},
                    resolution_id=workflow.id,
                )
            elif approval.status == ApprovalStatus.PENDING:
                # Still waiting for human review
                workflow.updated_at = datetime.utcnow()
            else:
                workflow.status = WorkflowStatus.FAILED
                workflow.errors.append(f"Unexpected approval status: {approval.status.value}")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(f"Failed to check approval status: {str(e)}")

        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _sync_order_status_for_refund(self, workflow: ResolutionWorkflow) -> Optional[str]:
        """Mark the order `refunded` once its refund has actually completed.

        issue_refund writes the refunds row and the idempotency ledger but
        leaves orders.status untouched, which made /console and /dashboard
        disagree with the money that had actually moved.

        Returns the new order status, or None if nothing was changed.
        """
        if not workflow.order_number:
            return None
        action = workflow.action_result or {}
        if action.get("status") not in ("completed", "duplicate"):
            return None
        try:
            client = get_supabase_client()
            client.table("orders") \
                .update({"status": "refunded"}) \
                .eq("order_number", workflow.order_number) \
                .execute()
            return "refunded"
        except Exception as e:
            # Never let bookkeeping failure mask a real, successful refund.
            workflow.errors.append(f"Warning: could not set order status to refunded: {e}")
            return None

    async def _step_mark_approval_executed(self, workflow: ResolutionWorkflow) -> None:
        """Flip the approval to `executed`, only after action + verification.

        Called after _step_verify succeeds, so the approval can never claim to
        be executed while no refund/order change actually exists.
        """
        approval_id = workflow.context.get("approval_id")
        if not approval_id:
            return
        try:
            await approval_service.transition_to_executed(approval_id)
        except Exception as e:
            # The DB approval_status enum currently has no 'executed' member;
            # surface it rather than pretending the transition happened.
            workflow.errors.append(f"Warning: could not mark approval executed: {e}")

    async def _step_execute(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 7: EXECUTE - Perform the authorized action."""
        if workflow.status == WorkflowStatus.PENDING_APPROVAL:
            workflow.errors.append("Cannot execute: waiting for approval")
            return workflow

        if workflow.status != WorkflowStatus.EXECUTING:
            return workflow

        workflow.status = WorkflowStatus.EXECUTING

        if workflow.intent == WorkflowIntent.REFUND_REQUEST and workflow.order_id:
            # Get refund amount from calculation
            refund_amount = None

            for call in workflow.tool_calls:
                if call.tool_name == "calculate_refund" and call.output_data:
                    calc = call.output_data.get("calculation", {})
                    if calc.get("eligible_amount"):
                        refund_amount = Decimal(str(calc["eligible_amount"]))
                        break

            # Generate operation_id using the actual calculated refund amount
            operation_id = (
                f"refund-order-{workflow.order_id}-{refund_amount}"
                if refund_amount
                else f"refund-order-{workflow.order_id}-0"
            )

            if refund_amount and refund_amount > 0:
                execute_result = await tool_registry.execute("issue_refund", {
                    "order_id": workflow.order_id,
                    "amount": str(refund_amount),
                    "operation_id": operation_id,
                    "reason": workflow.policy_result.reason if workflow.policy_result else "Policy-approved refund"
                })
                await self._record_tool_call(
                    workflow, "issue_refund", 
                    {"order_id": workflow.order_id, "amount": str(refund_amount), "operation_id": operation_id},
                    execute_result.data if execute_result.success else None,
                    execute_result.success, execute_result.error.message if execute_result.error else None
                )

                if execute_result.success:
                    workflow.action_result = execute_result.data.get("result")

                    # Keep the order lifecycle in step with the money movement.
                    # cancel_order already sets `cancelled`; issue_refund does
                    # not, so mirror it here for the refund path.
                    new_order_status = await self._sync_order_status_for_refund(workflow)

                    # Record action executed
                    await audit_service.record_event_simple(
                        request_id=workflow.request_id,
                        event_type=AuditEventType.ACTION_EXECUTED,
                        event_data={
                            "action": "issue_refund",
                            "order_id": workflow.order_id,
                            "amount": str(refund_amount),
                            "operation_id": operation_id,
                            "order_status_after": new_order_status,
                        },
                        resolution_id=workflow.id,
                    )
                else:
                    workflow.status = WorkflowStatus.FAILED
                    workflow.errors.append(f"Refund execution failed: {execute_result.error.message if execute_result.error else 'Unknown error'}")

                    await audit_service.record_event_simple(
                        request_id=workflow.request_id,
                        event_type=AuditEventType.WORKFLOW_FAILED,
                        event_data={"reason": "Refund execution failed", "error": execute_result.error.message if execute_result.error else "Unknown error"},
                        resolution_id=workflow.id,
                    )

        elif workflow.intent == WorkflowIntent.CANCELLATION_REQUEST and workflow.order_id:
            operation_id = f"cancel-order-{workflow.order_id}"
            execute_result = await tool_registry.execute("cancel_order", {
                "order_id": workflow.order_id,
                "operation_id": operation_id,
                "reason": "Customer requested cancellation"
            })
            await self._record_tool_call(
                workflow, "cancel_order",
                {"order_id": workflow.order_id, "operation_id": operation_id},
                execute_result.data if execute_result.success else None,
                execute_result.success, execute_result.error.message if execute_result.error else None
            )

            if execute_result.success:
                workflow.action_result = execute_result.data.get("result")

                # Record action executed
                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.ACTION_EXECUTED,
                    event_data={
                        "action": "cancel_order",
                        "order_id": workflow.order_id,
                        "operation_id": operation_id,
                    },
                    resolution_id=workflow.id,
                )
            else:
                workflow.status = WorkflowStatus.FAILED
                workflow.errors.append(f"Cancellation failed: {execute_result.error.message if execute_result.error else 'Unknown error'}")

                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.WORKFLOW_FAILED,
                    event_data={"reason": "Cancellation failed", "error": execute_result.error.message if execute_result.error else "Unknown error"},
                    resolution_id=workflow.id,
                )

        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _step_verify(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 8: VERIFY - Verify the action succeeded."""
        if workflow.status != WorkflowStatus.EXECUTING and workflow.status != WorkflowStatus.VERIFYING:
            return workflow

        workflow.status = WorkflowStatus.VERIFYING

        # For refunds, verify by re-reading the actual refunds row.
        # Deliberately does NOT trust the tool's returned status or the
        # idempotency ledger: an earlier version accepted any non-empty
        # refund_id and reported verified=true even when no refund existed.
        if workflow.intent == WorkflowIntent.REFUND_REQUEST and workflow.action_result:
            refund_id = workflow.action_result.get("refund_id")
            if not refund_id:
                workflow.verification = VerificationRecord(
                    success=False,
                    error="No refund ID returned",
                )
            else:
                try:
                    client = get_supabase_client()
                    found = (
                        client.table("refunds")
                        .select("id, order_id, amount, currency, status, operation_id")
                        .eq("id", refund_id)
                        .limit(1)
                        .execute()
                    )
                    row = (found.data or [None])[0]

                    if row is None:
                        workflow.verification = VerificationRecord(
                            success=False,
                            details={"refund_id": refund_id, "refund_row_found": False},
                            error=f"Refund {refund_id} does not exist in the refunds table",
                        )
                    else:
                        # The refund must belong to this order and be settled.
                        expected_amount = None
                        for call in workflow.tool_calls:
                            if call.tool_name == "calculate_refund" and call.output_data:
                                calc = call.output_data.get("calculation", {})
                                if calc.get("eligible_amount") is not None:
                                    expected_amount = Decimal(str(calc["eligible_amount"]))
                                    break
                        actual_amount = Decimal(str(row.get("amount")))
                        amount_ok = expected_amount is None or actual_amount == expected_amount
                        order_ok = True
                        if workflow.order_number:
                            order_uuid = await self._get_order_uuid(workflow.order_number)
                            order_ok = order_uuid is None or row.get("order_id") == order_uuid
                        status_ok = row.get("status") == "completed"
                        success = amount_ok and order_ok and status_ok

                        reasons = []
                        if not status_ok:
                            reasons.append(f"refund status is {row.get('status')}, not completed")
                        if not amount_ok:
                            reasons.append(f"refund amount {actual_amount} != expected {expected_amount}")
                        if not order_ok:
                            reasons.append("refund is not linked to this order")

                        workflow.verification = VerificationRecord(
                            success=success,
                            details={
                                "refund_id": refund_id,
                                "refund_row_found": True,
                                "refund_status": row.get("status"),
                                "refund_amount": str(actual_amount),
                                "expected_amount": str(expected_amount) if expected_amount is not None else None,
                                "order_id": row.get("order_id"),
                                "operation_id": row.get("operation_id"),
                                "verified": success,
                            },
                            error=None if success else "; ".join(reasons),
                        )

                        await audit_service.record_event_simple(
                            request_id=workflow.request_id,
                            event_type=AuditEventType.ACTION_VERIFIED,
                            event_data={
                                "refund_id": refund_id,
                                "refund_row_found": True,
                                "refund_status": row.get("status"),
                                "verified": success,
                            },
                            resolution_id=workflow.id,
                        )
                except Exception as e:
                    workflow.verification = VerificationRecord(
                        success=False,
                        details={"refund_id": refund_id},
                        error=f"Verification query failed: {str(e)}",
                    )

        # For cancellations, verify by checking order status
        elif workflow.intent == WorkflowIntent.CANCELLATION_REQUEST and workflow.order_id:
            order_result = await tool_registry.execute("get_order", {"order_id": workflow.order_id})
            if order_result.success:
                order_status = order_result.data["order"]["status"]
                success = order_status == "cancelled"
                workflow.verification = VerificationRecord(
                    success=success,
                    details={"order_status": order_status},
                    error=None if success else f"Order status is {order_status}, not cancelled"
                )

                # Record action verified
                await audit_service.record_event_simple(
                    request_id=workflow.request_id,
                    event_type=AuditEventType.ACTION_VERIFIED,
                    event_data={"order_id": workflow.order_id, "order_status": order_status, "verified": success},
                    resolution_id=workflow.id,
                )
            else:
                workflow.verification = VerificationRecord(
                    success=False,
                    error="Failed to verify order status"
                )

        if workflow.verification and not workflow.verification.success:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(f"Verification failed: {workflow.verification.error}")
            # If we had an approval, mark it as failed
            approval_id = workflow.context.get("approval_id")
            if approval_id:
                try:
                    await approval_service.transition_to_failed(approval_id, workflow.verification.error)
                except Exception:
                    pass  # Best effort

            # Record workflow failed
            await audit_service.record_event_simple(
                request_id=workflow.request_id,
                event_type=AuditEventType.WORKFLOW_FAILED,
                event_data={"reason": "Verification failed", "error": workflow.verification.error},
                resolution_id=workflow.id,
            )

        workflow.updated_at = datetime.utcnow()
        return workflow

    async def _step_complete(self, workflow: ResolutionWorkflow) -> ResolutionWorkflow:
        """Step 9: COMPLETE - Finalize workflow."""
        # If there's a pending approval, we can't complete
        if workflow.status == WorkflowStatus.PENDING_APPROVAL:
            return workflow

        workflow.status = WorkflowStatus.COMPLETED
        workflow.final_status = "completed"
        workflow.completed_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()

        # Record workflow completed
        await audit_service.record_event_simple(
            request_id=workflow.request_id,
            event_type=AuditEventType.WORKFLOW_COMPLETED,
            event_data={"final_status": workflow.final_status},
            resolution_id=workflow.id,
        )
        return workflow

    def build_response(self, workflow: ResolutionWorkflow) -> ResolutionResponse:
        """Build API response from workflow state."""
        policy_decision = None
        policy_reason = None
        approval_required = False
        approval_tier = None
        action_taken = None
        action_result = None
        verification_result = None

        if workflow.policy_result:
            policy_decision = workflow.policy_result.decision
            policy_reason = workflow.policy_result.reason
            approval_required = workflow.policy_result.decision == "REQUIRES_APPROVAL"
            approval_tier = workflow.policy_result.approval_tier

        if workflow.action_result:
            action_taken = workflow.intent.value
            action_result = workflow.action_result
            idempotent_replay = action_result.get("idempotent_replay", False) if isinstance(action_result, dict) else False
        else:
            idempotent_replay = False

        if workflow.verification:
            verification_result = {
                "success": workflow.verification.success,
                "verified_at": workflow.verification.verified_at.isoformat() if workflow.verification.verified_at else None,
                "details": workflow.verification.details,
                "error": workflow.verification.error,
            }

        # Generate final message
        if workflow.status == WorkflowStatus.COMPLETED:
            if workflow.intent == WorkflowIntent.REFUND_REQUEST:
                final_message = f"Refund processed successfully for order {workflow.order_number}."
            elif workflow.intent == WorkflowIntent.CANCELLATION_REQUEST:
                final_message = f"Order {workflow.order_number} has been cancelled."
            else:
                final_message = "Request completed successfully."
        elif workflow.status == WorkflowStatus.REJECTED:
            final_message = f"Request rejected: {workflow.errors[-1] if workflow.errors else 'Policy violation'}"
        elif workflow.status == WorkflowStatus.PENDING_APPROVAL:
            # ApprovalRecord has no approval_tier field; the tier comes from the
            # policy decision captured above in `approval_tier`.
            final_message = f"Request requires {approval_tier or 'manager'} approval. Awaiting human review."
        elif workflow.status == WorkflowStatus.FAILED:
            final_message = f"Request failed: {workflow.errors[-1] if workflow.errors else 'Unknown error'}"
        else:
            final_message = f"Request is {workflow.status.value}."

        return ResolutionResponse(
            workflow_id=workflow.id,
            request_id=workflow.request_id,
            status=workflow.status,
            intent=workflow.intent,
            user_request=workflow.user_request,
            order_id=workflow.order_id,
            order_number=workflow.order_number,
            policy_decision=policy_decision,
            policy_reason=policy_reason,
            approval_required=approval_required,
            approval_tier=approval_tier,
            action_taken=action_taken,
            action_result=action_result,
            verification_result=verification_result,
            final_message=final_message,
            errors=workflow.errors,
            idempotent_replay=idempotent_replay,
        )


# Singleton instance
workflow_engine = WorkflowEngine()