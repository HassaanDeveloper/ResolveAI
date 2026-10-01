from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from app.tools.base import BaseTool, ToolInput, ToolOutput
from app.tools.schemas.base import RefundIssueResult, ToolResult
from app.reliability import idempotency_service, OperationStatus


class IssueRefundInput(ToolInput):
    order_id: str = Field(..., description="Order number (e.g., '10482')")
    amount: Decimal = Field(..., gt=0, description="Refund amount")
    operation_id: str = Field(..., description="Idempotency key (e.g., 'refund-order-10482-74.99')")
    reason: str = Field(default="Policy-eligible refund", description="Reason for refund")


class IssueRefundOutput(ToolOutput):
    result: Optional[RefundIssueResult] = None
    error: Optional[str] = None


class IssueRefundTool(BaseTool):
    name = "issue_refund"
    category = "side_effect"
    description = "Issue a refund for an order (requires policy approval)"
    requires_approval = True
    input_schema = IssueRefundInput
    output_schema = IssueRefundOutput

    async def _replay_existing_refund(self, input_data: IssueRefundInput, supabase) -> Optional[ToolResult]:
        """
        If a refund row already exists for this operation_id, replay it as a success.

        A previous attempt may have written the refund row and then failed afterwards,
        which would otherwise leave a cached "failed" ledger entry that blocks the
        operation forever. Returns None when no refund row exists.
        """
        import logging
        from datetime import datetime, timezone

        logger = logging.getLogger(__name__)

        try:
            existing = supabase.table("refunds").select(
                "id, order_id, amount, currency, status, operation_id, processed_at"
            ).eq("operation_id", input_data.operation_id).limit(1).execute()
        except Exception as e:
            logger.warning(f"Could not read refunds for operation_id={input_data.operation_id}: {e}")
            return None

        row = (existing.data or [None])[0]
        if not row:
            return None

        processed_at = row.get("processed_at") or datetime.now(timezone.utc).isoformat()

        # The operation is being confirmed as executed, so complete the refund record
        # that a previous attempt left in flight.
        if row.get("status") != "completed":
            supabase.table("refunds").update({
                "status": "completed",
                "processed_at": processed_at
            }).eq("id", row["id"]).execute()

        await idempotency_service.mark_executed(input_data.operation_id, {
            "refund_id": row["id"],
            "currency": row.get("currency", "USD"),
            "processed_at": processed_at
        })

        return self.success_result(IssueRefundOutput(result=RefundIssueResult(
            success=True,
            refund_id=row["id"],
            operation_id=input_data.operation_id,
            amount=Decimal(str(row.get("amount", input_data.amount))),
            currency=row.get("currency", "USD"),
            status="duplicate",
            message="Refund already exists (idempotent replay)",
            processed_at=processed_at,
            idempotent_replay=True
        )))

    async def execute(self, input_data: IssueRefundInput) -> ToolResult:
        from app.services.database import get_supabase_client
        from datetime import datetime, timezone
        import logging

        logger = logging.getLogger(__name__)
        
        try:
            supabase = get_supabase_client()

            # Check idempotency using the new service
            existing_result = await idempotency_service.check_idempotency(input_data.operation_id)
            stale_failure = False
            if existing_result:
                if existing_result.idempotent and existing_result.success:
                    result_data = existing_result.data or {}
                    return self.success_result(IssueRefundOutput(result=RefundIssueResult(
                        success=True,
                        refund_id=result_data.get("refund_id"),
                        operation_id=input_data.operation_id,
                        amount=input_data.amount,
                        currency=result_data.get("currency", "USD"),
                        status="duplicate",
                        message="Refund already processed (idempotent)",
                        processed_at=result_data.get("processed_at"),
                        idempotent_replay=True
                    )))
                elif existing_result.idempotent and not existing_result.success:
                    # A cached failure is not necessarily terminal: a previous attempt may
                    # have written the refund row before failing. Always check the refunds
                    # table before reporting a conflict, and never return the stored
                    # database error text to the caller.
                    logger.warning(
                        f"Cached failure for operation_id={input_data.operation_id}: {existing_result.error}"
                    )
                    replay = await self._replay_existing_refund(input_data, supabase)
                    if replay is not None:
                        return replay

                    # No refund row exists, so the cached failure is stale and this
                    # operation is genuinely retryable. Clear it and re-attempt with the
                    # same operation_id.
                    if await idempotency_service.reset_operation(input_data.operation_id):
                        logger.info(
                            f"Cleared stale failure for operation_id={input_data.operation_id}; re-attempting"
                        )
                        stale_failure = True
                    else:
                        return self.error_result(
                            "CONFLICT",
                            f"Refund for operation {input_data.operation_id} previously failed. "
                            "No refund was recorded; please contact support."
                        )
                else:
                    return self.error_result("CONFLICT", f"Operation {input_data.operation_id} is already in progress")

            # Reserve the operation (skipped when a stale failure was just cleared,
            # because the ledger row is reused rather than re-inserted)
            if not stale_failure:
                reserved = await idempotency_service.reserve_operation(input_data.operation_id, "issue_refund")
                if not reserved:
                    return self.error_result("CONFLICT", f"Operation {input_data.operation_id} already exists")

            try:
                # Get order
                order_response = supabase.table("orders").select("id, order_number, total_amount, currency").eq("order_number", input_data.order_id).single().execute()
                
                if not order_response.data:
                    await idempotency_service.mark_failed(input_data.operation_id, f"Order {input_data.order_id} not found")
                    return self.error_result("NOT_FOUND", f"Order {input_data.order_id} not found")

                order = order_response.data
                
                # Validate amount doesn't exceed order total
                if input_data.amount > Decimal(str(order["total_amount"])):
                    await idempotency_service.mark_failed(input_data.operation_id, "Refund amount exceeds order total")
                    return self.error_result("VALIDATION_ERROR", "Refund amount exceeds order total")

                # Check for existing completed refunds
                refund_response = supabase.table("refunds").select("amount, status").eq("order_id", order["id"]).execute()
                existing_refunds = sum(Decimal(str(r["amount"])) for r in refund_response.data if r["status"] == "completed") if refund_response.data else Decimal("0")
                
                if existing_refunds + input_data.amount > Decimal(str(order["total_amount"])):
                    await idempotency_service.mark_failed(input_data.operation_id, "Total refunds would exceed order amount")
                    return self.error_result("VALIDATION_ERROR", "Total refunds would exceed order amount")

                # Pre-check: look for existing refund with same operation_id in refunds table
                # This handles the case where seed data or a previous run inserted a refund
                # but the operations table didn't get a corresponding entry.
                # NOTE: .limit(1) is required - .single() raises PGRST116 when no row exists.
                existing_refund = supabase.table("refunds").select("id, order_id, amount, currency, status, operation_id, processed_at").eq("operation_id", input_data.operation_id).limit(1).execute()
                existing_refund_row = (existing_refund.data or [None])[0]
                if existing_refund_row:
                    replay = await self._replay_existing_refund(input_data, supabase)
                    if replay is not None:
                        return replay

                # Mark as executing
                await idempotency_service.mark_executing(input_data.operation_id)

                # Create refund record
                refund_data = {
                    "order_id": order["id"],
                    "amount": float(input_data.amount),
                    "currency": order["currency"],
                    "status": "processing",
                    "operation_id": input_data.operation_id
                }
                
                try:
                    refund_response = supabase.table("refunds").insert(refund_data).execute()
                except Exception as insert_error:
                    # If insert fails due to unique constraint, the refund already exists
                    # Query it and return as idempotent replay
                    if "unique" in str(insert_error).lower() or "duplicate" in str(insert_error).lower() or "constraint" in str(insert_error).lower():
                        # Full database detail stays server-side; the client only ever
                        # sees the idempotent replay result.
                        logger.warning(f"Idempotent replay: refund with operation_id={input_data.operation_id} already exists in DB: {str(insert_error)}")
                        replay = await self._replay_existing_refund(input_data, supabase)
                        if replay is not None:
                            return replay
                    logger.error(f"Unexpected DB error inserting refund for operation_id={input_data.operation_id}: {str(insert_error)}")
                    await idempotency_service.mark_failed(input_data.operation_id, "Internal processing error")
                    return self.error_result("EXECUTION_ERROR", "An internal error occurred while processing your refund")

                if not refund_response.data:
                    await idempotency_service.mark_failed(input_data.operation_id, "Failed to create refund record")
                    return self.error_result("EXECUTION_ERROR", "Failed to create refund record")

                refund_id = refund_response.data[0]["id"]
                processed_at = datetime.now(timezone.utc)

                # Simulate processing (in real system, this would call payment processor)
                # For now, mark as completed
                supabase.table("refunds").update({
                    "status": "completed",
                    "processed_at": processed_at.isoformat()
                }).eq("id", refund_id).execute()

                # Mark operation as executed
                result_data = {
                    "refund_id": refund_id,
                    "currency": order["currency"],
                    "processed_at": processed_at.isoformat()
                }
                await idempotency_service.mark_executed(input_data.operation_id, result_data)

                return self.success_result(IssueRefundOutput(result=RefundIssueResult(
                    success=True,
                    refund_id=refund_id,
                    operation_id=input_data.operation_id,
                    amount=input_data.amount,
                    currency=order["currency"],
                    status="completed",
                    message="Refund processed successfully",
                    processed_at=processed_at,
                    idempotent_replay=False
                )))

            except Exception as e:
                logger.error(f"Unexpected error in issue_refund for operation_id={input_data.operation_id}: {str(e)}")
                await idempotency_service.mark_failed(input_data.operation_id, "Internal processing error")
                return self.error_result("EXECUTION_ERROR", "An internal error occurred while processing your refund")

        except Exception as e:
            logger.error(f"Critical error in issue_refund: {str(e)}")
            try:
                await idempotency_service.mark_failed(input_data.operation_id, "Internal processing error")
            except:
                pass
            return self.error_result("EXECUTION_ERROR", "An internal error occurred while processing your refund")


issue_refund_tool = IssueRefundTool()
