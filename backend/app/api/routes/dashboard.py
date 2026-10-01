from fastapi import APIRouter
from datetime import timezone

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def get_dashboard_metrics():
    """
    Get dashboard metrics from the audit/workflow data.
    
    Returns:
    - total_requests: Total number of resolution requests
    - successful_resolutions: Number of completed resolutions
    - pending_approvals: Number of pending items (traces awaiting action + approvals pending)
    - failed_resolutions: Number of failed/rejected resolutions
    - avg_resolution_time_ms: Average resolution time in milliseconds (null if not enough data)
    """
    from app.audit.service import audit_service
    
    # Get all workflow traces
    traces = await audit_service.list_workflow_traces(page_size=10000)
    
    total_requests = len(traces)
    successful_resolutions = sum(1 for t in traces if t.status == "completed")
    failed_resolutions = sum(1 for t in traces if t.status in ["rejected", "failed"])
    
    # Count pending items: traces with pending/pending_approval status + pending approvals
    # (avoid double-counting pending_approval traces that have corresponding approval records)
    pending_traces = sum(1 for t in traces if t.status == "pending")
    pending_approval_trace_ids = {t.workflow_id for t in traces if t.status == "pending_approval"}
    
    from app.approvals.service import approval_service
    approvals_result = await approval_service.list_approvals(status=None, page=1, page_size=10000)
    pending_approvals_db = sum(
        1 for a in approvals_result.approvals
        if a.status == "pending" and a.resolution_id not in pending_approval_trace_ids
    )
    
    pending_approvals = pending_traces + len(pending_approval_trace_ids) + pending_approvals_db
    
    # Calculate average resolution time for completed workflows with valid timestamps
    completed_traces = [t for t in traces if t.status == "completed" and t.completed_at and t.created_at]
    avg_resolution_time_ms = None
    if completed_traces:
        total_ms = 0.0
        measured = 0
        for t in completed_traces:
            try:
                # WorkflowTrace already parses these into datetime objects, so
                # they are subtracted directly. Stricter ISO parsing here used
                # to raise TypeError and silently zero out the average.
                created = t.created_at
                completed = t.completed_at
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if completed.tzinfo is None:
                    completed = completed.replace(tzinfo=timezone.utc)
                delta = (completed - created).total_seconds() * 1000
                if delta < 0:
                    continue
                total_ms += delta
                measured += 1
            except Exception:
                continue
        avg_resolution_time_ms = int(total_ms / measured) if measured else None
    
    return {
        "total_requests": total_requests,
        "successful_resolutions": successful_resolutions,
        "pending_approvals": pending_approvals,
        "failed_resolutions": failed_resolutions,
        "avg_resolution_time_ms": avg_resolution_time_ms,
    }