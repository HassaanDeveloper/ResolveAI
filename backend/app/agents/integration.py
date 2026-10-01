"""
Agent integration with the workflow engine.
This module connects the bounded agent to the existing workflow.
"""
from typing import Optional
from app.workflows.models import ResolutionWorkflow, ResolutionRequest, ResolutionResponse, WorkflowStatus, WorkflowIntent
from app.agents.core import run_agent, AgentConfig
from app.agents.models import AgentState
from app.workflows.engine import workflow_engine
from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_agent_enhanced_workflow(
    request: ResolutionRequest,
    config: Optional[AgentConfig] = None
) -> ResolutionResponse:
    """
    Run the enhanced workflow with agent intelligence.
    
    This replaces the deterministic workflow with agent-driven investigation
    for the UNDERSTAND, INVESTIGATE, RETRIEVE POLICY, and DECIDE steps.
    """
    # Step 1: Run agent for investigation phase
    agent_state = await run_agent(
        request_id=request.request_id,
        user_request=request.user_request,
        order_id=request.order_id,
        customer_id=request.customer_id,
        config=config
    )
    
    # Step 2: Create workflow from agent state
    workflow = await _create_workflow_from_agent(agent_state, request)
    
    # Step 3: Continue with policy check and execution (deterministic)
    workflow = await workflow_engine._step_policy_check(workflow)
    
    if workflow.status in [WorkflowStatus.REJECTED, WorkflowStatus.FAILED]:
        return workflow_engine.build_response(workflow)
    
    if workflow.status == WorkflowStatus.PENDING_APPROVAL:
        return workflow_engine.build_response(workflow)
    
    # Execute if allowed
    workflow = await workflow_engine._step_execute(workflow)
    
    if workflow.status == WorkflowStatus.FAILED:
        return workflow_engine.build_response(workflow)
    
    # Verify
    workflow = await workflow_engine._step_verify(workflow)
    
    # Complete
    workflow = await workflow_engine._step_complete(workflow)
    
    return workflow_engine.build_response(workflow)


async def _create_workflow_from_agent(
    agent_state: AgentState,
    request: ResolutionRequest
) -> ResolutionWorkflow:
    """Create a workflow state from the agent's investigation results."""
    workflow = ResolutionWorkflow(
        request_id=request.request_id,
        user_request=request.user_request,
        customer_id=request.customer_id,
        order_id=agent_state.order_id,
    )
    
    # Copy agent findings to workflow
    workflow.intent = _classify_intent_from_agent(agent_state)
    workflow.order_number = agent_state.order_id
    workflow.retrieved_documents = agent_state.evidence
    workflow.tool_calls = [
        {
            "tool_name": obs.tool_name,
            "input_data": {"note": "See evidence for details"},
            "output_data": obs.output,
            "success": obs.success,
            "error": obs.error,
            "timestamp": obs.timestamp.isoformat() if obs.timestamp else None
        }
        for obs in agent_state.observations
    ]
    
    return workflow


def _classify_intent_from_agent(agent_state: AgentState) -> str:
    """Classify intent from agent state."""
    if agent_state.intent:
        return agent_state.intent
    
    # Infer from user request
    request_lower = agent_state.user_request.lower()
    if any(kw in request_lower for kw in ["refund", "money back", "return money"]):
        return "refund_request"
    elif any(kw in request_lower for kw in ["cancel", "cancellation", "stop order"]):
        return "cancellation_request"
    elif any(kw in request_lower for kw in ["where is", "shipping", "delivery", "track", "arrived"]):
        return "shipping_inquiry"
    elif any(kw in request_lower for kw in ["escalate", "manager", "supervisor", "complaint"]):
        return "escalation_request"
    return "unknown"


async def run_agent_only_investigation(request: ResolutionRequest) -> AgentState:
    """
    Run just the agent investigation phase.
    Useful for testing and debugging.
    """
    return await run_agent(
        request_id=request.request_id,
        user_request=request.user_request,
        order_id=request.order_id,
        customer_id=request.customer_id,
    )