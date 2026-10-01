import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.audit.models import (
    AuditEvent,
    AuditEventCreate,
    AuditEventType,
    AuditLogResponse,
    WorkflowTrace,
    VerificationResult,
    TraceResponse,
)
from app.services.database import get_supabase_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service for recording and retrieving audit events and workflow traces."""

    def __init__(self):
        self.supabase = None

    def _get_client(self):
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase

    async def record_event(self, event: AuditEventCreate) -> AuditEvent:
        """Record an audit event."""
        client = self._get_client()

        event_id = str(uuid.uuid4())
        now = datetime.utcnow()

        data = {
            "id": event_id,
            "request_id": event.request_id,
            "resolution_id": event.resolution_id,
            "event_type": event.event_type.value,
            "event_data": event.event_data,
            "created_at": now.isoformat(),
        }

        result = client.table("audit_events").insert(data).execute()

        if not result.data:
            raise Exception("Failed to record audit event")

        recorded = result.data[0]
        logger.info(f"Recorded audit event: {event.event_type.value} for request {event.request_id}")

        return AuditEvent(
            id=recorded["id"],
            request_id=recorded["request_id"],
            resolution_id=recorded.get("resolution_id"),
            event_type=AuditEventType(recorded["event_type"]),
            event_data=recorded.get("event_data", {}),
            created_at=recorded["created_at"],
        )

    async def record_event_simple(
        self,
        request_id: str,
        event_type: AuditEventType,
        event_data: Dict[str, Any] = None,
        resolution_id: Optional[str] = None,
    ) -> AuditEvent:
        """Convenience method to record an event with minimal parameters."""
        return await self.record_event(AuditEventCreate(
            request_id=request_id,
            resolution_id=resolution_id,
            event_type=event_type,
            event_data=event_data or {}
        ))

    async def get_events(
        self,
        request_id: Optional[str] = None,
        resolution_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[AuditEvent]:
        """Retrieve audit events with optional filtering."""
        client = self._get_client()

        query = client.table("audit_events").select("*")

        if request_id:
            query = query.eq("request_id", request_id)
        if resolution_id:
            query = query.eq("resolution_id", resolution_id)
        if event_type:
            query = query.eq("event_type", event_type.value)

        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1).order("created_at", desc=True)

        result = query.execute()

        events = []
        for row in (result.data or []):
            events.append(AuditEvent(
                id=row["id"],
                request_id=row["request_id"],
                resolution_id=row.get("resolution_id"),
                event_type=AuditEventType(row["event_type"]),
                event_data=row.get("event_data", {}),
                created_at=row["created_at"],
            ))

        return events

    async def get_workflow_trace(self, workflow_id: str) -> Optional[WorkflowTrace]:
        """Retrieve a complete workflow trace from the resolutions table."""
        client = self._get_client()

        # First get the workflow from resolutions
        workflow_result = client.table("resolutions").select("*").eq("id", workflow_id).single().execute()

        if not workflow_result.data:
            return None

        w = workflow_result.data

        # Get associated audit events
        events = await self.get_events(resolution_id=workflow_id)

        return WorkflowTrace(
            workflow_id=w["id"],
            request_id=w["request_id"],
            user_request=w["user_request"],
            intent=w.get("intent"),
            status=w["status"],
            order_id=w.get("order_id"),
            order_number=w.get("order_number"),
            retrieved_documents=w.get("retrieved_documents", []),
            tool_calls=w.get("tool_calls", []),
            policy_result=w.get("policy_result"),
            approval=w.get("approval"),
            action_result=w.get("action_result"),
            verification=None,  # Verification stored separately if needed
            final_status=w.get("final_status"),
            errors=w.get("errors", []),
            created_at=w["created_at"],
            updated_at=w["updated_at"],
            completed_at=w.get("completed_at"),
        )

    async def get_trace_with_events(self, workflow_id: str) -> Optional[TraceResponse]:
        """Get complete workflow trace with associated audit events."""
        trace = await self.get_workflow_trace(workflow_id)
        if not trace:
            return None

        events = await self.get_events(resolution_id=workflow_id)
        return TraceResponse(trace=trace, audit_events=events)

    async def list_workflow_traces(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[WorkflowTrace]:
        """List workflow traces with optional filtering."""
        client = self._get_client()

        query = client.table("resolutions").select("*")

        if status:
            query = query.eq("status", status)

        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1).order("created_at", desc=True)

        result = query.execute()

        traces = []
        for row in (result.data or []):
            traces.append(WorkflowTrace(
                workflow_id=row["id"],
                request_id=row["request_id"],
                user_request=row["user_request"],
                intent=row.get("intent"),
                status=row["status"],
                order_id=row.get("order_id"),
                order_number=row.get("order_number"),
                retrieved_documents=row.get("retrieved_documents", []),
                tool_calls=row.get("tool_calls", []),
                policy_result=row.get("policy_result"),
                approval=row.get("approval"),
                action_result=row.get("action_result"),
                verification=None,
                final_status=row.get("final_status"),
                errors=row.get("errors", []),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                completed_at=row.get("completed_at"),
            ))

        return traces


# Singleton instance
audit_service = AuditService()