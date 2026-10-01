from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pydantic import BaseModel, Field

from app.approvals.service import approval_service
from app.approvals.models import (
    ApprovalCreate,
    ApprovalDecision,
    ApprovalResponse,
    ApprovalListResponse,
    ApprovalStatus,
    ApprovalActionType,
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApproveRequest(BaseModel):
    decision: ApprovalStatus = Field(..., description="APPROVED or REJECTED")
    decided_by: str = Field(default="human_operator", description="Approver identifier")
    reason: Optional[str] = Field(None, description="Reason for decision")


@router.post("", response_model=ApprovalResponse, status_code=201)
async def create_approval(request: ApprovalCreate):
    """
    Create a new approval request.
    
    This is typically called by the workflow engine when the policy engine
    returns REQUIRES_APPROVAL.
    """
    try:
        return await approval_service.create_approval(request)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create approval: {str(e)}")


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    status: Optional[ApprovalStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List approval requests with optional filtering.
    """
    try:
        return await approval_service.list_approvals(status=status, page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list approvals: {str(e)}")


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str):
    """
    Get approval request details by ID.
    """
    try:
        return await approval_service.get_approval(approval_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval: {str(e)}")


@router.post("/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(approval_id: str, request: ApproveRequest):
    """
    Approve or reject an approval request.
    
    This is the human-in-the-loop decision point.
    """
    try:
        if request.decision not in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            raise HTTPException(status_code=422, detail="Decision must be APPROVED or REJECTED")
        
        decision = ApprovalDecision(
            approval_id=approval_id,
            decision=request.decision,
            decided_by=request.decided_by,
            reason=request.reason,
        )
        
        return await approval_service.decide_approval(decision)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decide approval: {str(e)}")


@router.post("/{approval_id}/execute", response_model=ApprovalResponse)
async def mark_executed(approval_id: str):
    """
    Mark an approved approval as executed.
    
    Called by the workflow engine after successful execution.
    """
    try:
        approval = await approval_service.transition_to_executed(approval_id)
        return ApprovalResponse(approval=approval, message="Approval marked as executed")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark executed: {str(e)}")


@router.post("/{approval_id}/fail", response_model=ApprovalResponse)
async def mark_failed(approval_id: str, reason: str = "Execution failed"):
    """
    Mark an approval as failed.
    
    Called by the workflow engine when execution fails.
    """
    try:
        approval = await approval_service.transition_to_failed(approval_id, reason)
        return ApprovalResponse(approval=approval, message="Approval marked as failed")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark failed: {str(e)}")


@router.get("/{approval_id}/detail", response_model=ApprovalResponse)
async def get_approval_detail(approval_id: str):
    """
    Get detailed approval information including the associated resolution context.
    """
    try:
        approval = await approval_service.get_approval(approval_id)
        
        # Get the associated resolution for context
        from app.audit.service import audit_service
        resolution = await audit_service.get_workflow_trace(approval.resolution_id)
        
        resolution_context = None
        if resolution:
            resolution_context = {
                "user_request": resolution.user_request,
                "intent": resolution.intent,
                "order_id": resolution.order_id,
                "order_number": resolution.order_number,
            }
        
        # Attach resolution context to the response
        return ApprovalResponse(
            approval=approval,
            message="Approval detail retrieved"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval detail: {str(e)}")