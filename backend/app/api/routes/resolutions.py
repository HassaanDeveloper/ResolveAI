from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

from app.workflows.engine import workflow_engine
from app.workflows.models import ResolutionRequest, ResolutionResponse, ResolutionWorkflow, WorkflowStatus
from app.core.exceptions import ValidationError


router = APIRouter(tags=["resolutions"])


class CreateResolutionRequest(BaseModel):
    user_request: str = Field(..., min_length=1, max_length=5000, description="User's resolution request")
    customer_id: Optional[str] = Field(None, description="Customer external ID (e.g., CUST-001)")
    order_id: Optional[str] = Field(None, description="Order number (e.g., 10482)")


class ResolutionStatusResponse(BaseModel):
    workflow_id: str
    request_id: str
    status: WorkflowStatus
    final_message: str


class ResolutionTraceResponse(ResolutionResponse):
    """Extended resolution response with full workflow trace for the console."""
    retrieved_documents: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    policy_result: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    errors: List[str] = []


def _build_trace_response(workflow: ResolutionWorkflow) -> ResolutionTraceResponse:
    """Build an extended trace response from the workflow."""
    base_response = workflow_engine.build_response(workflow)
    
    # Convert tool calls to dict format
    tool_calls = []
    for call in workflow.tool_calls:
        tool_calls.append({
            "tool": call.tool_name,
            "input": call.input_data,
            "success": call.success,
            "output": call.output_data,
            "error": call.error,
            "timestamp": call.timestamp.isoformat() if call.timestamp else None,
        })
    
    # Convert retrieved documents
    retrieved_documents = workflow.retrieved_documents
    
    # Convert policy result
    policy_result = None
    if workflow.policy_result:
        policy_result = {
            "action_type": workflow.policy_result.action_type,
            "decision": workflow.policy_result.decision,
            "reason": workflow.policy_result.reason,
            "policy_rule": workflow.policy_result.policy_rule,
            "risk_level": workflow.policy_result.risk_level,
            "approval_tier": workflow.policy_result.approval_tier,
            "conditions": workflow.policy_result.conditions,
        }
    
    # Convert approval
    approval = None
    if workflow.approval:
        approval = {
            "approval_id": workflow.approval.approval_id,
            "status": workflow.approval.status,
            "requested_at": workflow.approval.requested_at.isoformat() if workflow.approval.requested_at else None,
            "decided_at": workflow.approval.decided_at.isoformat() if workflow.approval.decided_at else None,
            "decided_by": workflow.approval.decided_by,
            "reason": workflow.approval.reason,
        }
    
    # Convert verification
    verification = None
    if workflow.verification:
        verification = {
            "success": workflow.verification.success,
            "verified_at": workflow.verification.verified_at.isoformat() if workflow.verification.verified_at else None,
            "details": workflow.verification.details,
            "error": workflow.verification.error,
        }
    
    return ResolutionTraceResponse(
        **base_response.model_dump(),
        retrieved_documents=retrieved_documents,
        tool_calls=tool_calls,
        policy_result=policy_result,
        approval=approval,
        verification=verification,
    )


@router.post("/", response_model=ResolutionTraceResponse)
async def create_resolution(request: CreateResolutionRequest, http_request: Request):
    """
    Create and execute a new resolution workflow.
    
    This endpoint accepts a user request and runs the full resolution workflow:
    - Extracts order ID from request
    - Classifies intent
    - Investigates order and shipping status
    - Retrieves relevant policies
    - Calculates refund (if applicable)
    - Runs deterministic policy engine
    - Executes action if approved
    - Verifies result
    """
    request_id = http_request.state.request_id if hasattr(http_request.state, 'request_id') else str(uuid.uuid4())
    
    resolution_request = ResolutionRequest(
        request_id=request_id,
        user_request=request.user_request,
        customer_id=request.customer_id,
        order_id=request.order_id,
    )

    workflow = await workflow_engine.execute(resolution_request)
    response = _build_trace_response(workflow)
    
    return response


@router.get("/{workflow_id}", response_model=ResolutionStatusResponse)
async def get_resolution_status(workflow_id: str):
    """
    Get the status of a resolution workflow.
    
    In a full implementation, this would query a workflow store.
    For now, returns a placeholder response.
    """
    # TODO: Implement workflow persistence and retrieval
    raise HTTPException(status_code=501, detail="Workflow status retrieval not yet implemented")


@router.post("/{workflow_id}/approve", response_model=ResolutionResponse)
async def approve_resolution(workflow_id: str, approver: str = "system"):
    """
    Approve a pending resolution workflow.
    
    This would continue the workflow execution after human approval.
    """
    # TODO: Implement approval workflow continuation
    raise HTTPException(status_code=501, detail="Approval workflow not yet implemented")


@router.post("/{workflow_id}/reject", response_model=ResolutionResponse)
async def reject_resolution(workflow_id: str, reason: str, rejector: str = "system"):
    """
    Reject a pending resolution workflow.
    """
    # TODO: Implement rejection workflow
    raise HTTPException(status_code=501, detail="Rejection workflow not yet implemented")