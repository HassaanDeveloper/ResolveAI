from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel, Field

from app.audit.service import audit_service
from app.audit.models import (
    AuditEvent,
    AuditEventCreate,
    AuditEventType,
    AuditLogResponse,
    WorkflowTrace,
    TraceResponse,
)

router = APIRouter(tags=["audit"])


class RecordEventRequest(BaseModel):
    request_id: str = Field(..., description="Request ID")
    resolution_id: Optional[str] = Field(None, description="Resolution/workflow ID")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    event_data: dict = Field(default_factory=dict, description="Event data")


@router.post("/events", response_model=AuditEvent, status_code=201)
async def record_audit_event(request: RecordEventRequest):
    """Record a new audit event."""
    try:
        event = AuditEventCreate(
            request_id=request.request_id,
            resolution_id=request.resolution_id,
            event_type=request.event_type,
            event_data=request.event_data,
        )
        return await audit_service.record_event(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record audit event: {str(e)}")


@router.get("/events", response_model=AuditLogResponse)
async def list_audit_events(
    request_id: Optional[str] = Query(None, description="Filter by request ID"),
    resolution_id: Optional[str] = Query(None, description="Filter by resolution/workflow ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List audit events with optional filtering."""
    try:
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid event type: {event_type}")

        events = await audit_service.get_events(
            request_id=request_id,
            resolution_id=resolution_id,
            event_type=event_type_enum,
            page=page,
            page_size=page_size,
        )

        # Get total count (simplified - in production would use count query)
        all_events = await audit_service.get_events(
            request_id=request_id,
            resolution_id=resolution_id,
            event_type=event_type_enum,
            page=1,
            page_size=10000,
        )

        return AuditLogResponse(
            events=events,
            total=len(all_events),
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list audit events: {str(e)}")


@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event(event_id: str):
    """Get a specific audit event by ID."""
    # This would require a direct lookup by ID
    # For now, return 501 as this requires a dedicated query
    raise HTTPException(status_code=501, detail="Get single event by ID not yet implemented")


@router.get("/traces", response_model=List[WorkflowTrace])
async def list_workflow_traces(
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List workflow traces with optional filtering."""
    try:
        traces = await audit_service.list_workflow_traces(
            status=status,
            page=page,
            page_size=page_size,
        )
        return traces
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflow traces: {str(e)}")


@router.get("/traces/{workflow_id}", response_model=TraceResponse)
async def get_workflow_trace(workflow_id: str):
    """Get complete workflow trace with associated audit events."""
    try:
        trace_response = await audit_service.get_trace_with_events(workflow_id)
        if not trace_response:
            raise HTTPException(status_code=404, detail="Workflow trace not found")
        return trace_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow trace: {str(e)}")