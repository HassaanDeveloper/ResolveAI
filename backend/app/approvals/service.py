import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.approvals.models import (
    ApprovalRequest,
    ApprovalCreate,
    ApprovalDecision,
    ApprovalResponse,
    ApprovalListItem,
    ApprovalListResponse,
    ApprovalStatus,
    ApprovalActionType,
    approval_from_db,
    approval_list_item_from_db,
)
from app.services.database import get_supabase_client
from app.core.logging import get_logger
from app.core.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)


class ApprovalService:
    """Service for managing human approval workflows."""

    def __init__(self):
        self.supabase = None

    def _get_client(self):
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase

    async def create_approval(self, approval_data: ApprovalCreate) -> ApprovalResponse:
        """Create a new approval request."""
        client = self._get_client()

        approval_id = str(uuid.uuid4())
        now = datetime.utcnow()

        data = {
            "id": approval_id,
            "resolution_id": approval_data.resolution_id,
            "action_type": approval_data.action_type.value,
            "action_payload": approval_data.action_payload,
            "reason": approval_data.reason,
            "policy_rule": approval_data.policy_rule,
            "risk_level": approval_data.risk_level,
            "status": ApprovalStatus.PENDING.value,
            "requested_at": now.isoformat(),
            "decided_at": None,
            "decided_by": None,
            "decision_reason": None,
        }

        result = client.table("approval_requests").insert(data).execute()

        if not result.data:
            raise ValidationError("Failed to create approval request")

        approval = approval_from_db(result.data[0])
        return ApprovalResponse(
            approval=approval,
            message="Approval request created and pending human review"
        )

    async def get_approval(self, approval_id: str) -> ApprovalRequest:
        """Get an approval request by ID."""
        client = self._get_client()

        result = client.table("approval_requests").select("*").eq("id", approval_id).single().execute()

        if not result.data:
            raise NotFoundError(f"Approval request {approval_id} not found")

        return approval_from_db(result.data)

    async def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ApprovalListResponse:
        """List approval requests with optional filtering."""
        client = self._get_client()

        query = client.table("approval_requests").select("*")

        if status:
            query = query.eq("status", status.value)

        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1).order("requested_at", desc=True)

        result = query.execute()

        approvals = [
            approval_list_item_from_db(row)
            for row in (result.data or [])
        ]

        return ApprovalListResponse(
            approvals=approvals,
            total=total,
            page=page,
            page_size=page_size
        )

    async def decide_approval(self, decision: ApprovalDecision) -> ApprovalResponse:
        """Approve or reject an approval request."""
        client = self._get_client()

        # Validate decision
        if decision.decision not in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            raise ValidationError("Decision must be APPROVED or REJECTED")

        # Get current approval
        current = await self.get_approval(decision.approval_id)

        if current.status != ApprovalStatus.PENDING:
            raise ValidationError(f"Approval request is not pending (current status: {current.status.value})")

        now = datetime.utcnow()

        update_data = {
            "status": decision.decision.value,
            "decided_at": now.isoformat(),
            "decided_by": decision.decided_by,
            "decision_reason": decision.reason,
        }

        result = client.table("approval_requests").update(update_data).eq("id", decision.approval_id).execute()

        if not result.data:
            raise ValidationError("Failed to update approval request")

        approval = approval_from_db(result.data[0])
        message = f"Approval request {decision.decision.value.lower()} by {decision.decided_by}"

        response = ApprovalResponse(approval=approval, message=message)

        # An approved decision is only half the job: the parked workflow must
        # now actually run the authorized action. A rejected decision runs the
        # same step chain, where _step_approval stops at REJECTED without ever
        # reaching the execute step, so the resolution ends in a real
        # `rejected` state instead of sitting at `pending_approval` forever.
        await self._resume_workflow(approval.resolution_id)

        return response

    async def _resume_workflow(self, resolution_id: Optional[str]) -> None:
        """Resume the parked workflow so an approved action really executes.

        Imported lazily to avoid a circular import: the workflow engine
        imports this module for approval lookups/transitions.
        """
        if not resolution_id:
            return
        try:
            from app.workflows.engine import workflow_engine
            await workflow_engine.resume_after_approval(resolution_id)
        except Exception as e:
            # Surface the failure rather than leaving a silently-approved row.
            logger.error(
                f"Failed to resume workflow for resolution {resolution_id} "
                f"after approval: {e}"
            )

    async def get_pending_for_resolution(self, resolution_id: str) -> Optional[ApprovalRequest]:
        """Get pending approval for a specific resolution."""
        client = self._get_client()

        result = client.table("approval_requests").select("*").eq("resolution_id", resolution_id).eq("status", ApprovalStatus.PENDING.value).single().execute()

        if not result.data:
            return None

        return approval_from_db(result.data)

    async def transition_to_executed(self, approval_id: str) -> ApprovalRequest:
        """Mark an approved approval as executed."""
        client = self._get_client()

        current = await self.get_approval(approval_id)

        if current.status != ApprovalStatus.APPROVED:
            raise ValidationError(f"Can only transition APPROVED to EXECUTED (current: {current.status.value})")

        update_data = {
            "status": ApprovalStatus.EXECUTED.value,
        }

        result = client.table("approval_requests").update(update_data).eq("id", approval_id).execute()

        if not result.data:
            raise ValidationError("Failed to transition approval to executed")

        return approval_from_db(result.data[0])

    async def transition_to_failed(self, approval_id: str, error_reason: str) -> ApprovalRequest:
        """Mark an approval as failed."""
        client = self._get_client()

        current = await self.get_approval(approval_id)

        if current.status not in [ApprovalStatus.APPROVED, ApprovalStatus.PENDING]:
            raise ValidationError(f"Cannot transition from {current.status.value} to FAILED")

        update_data = {
            "status": ApprovalStatus.FAILED.value,
            "decision_reason": error_reason,
        }

        result = client.table("approval_requests").update(update_data).eq("id", approval_id).execute()

        if not result.data:
            raise ValidationError("Failed to transition approval to failed")

        return approval_from_db(result.data[0])


# Singleton instance
approval_service = ApprovalService()