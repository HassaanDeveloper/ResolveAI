import asyncio
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import google.generativeai as genai
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import get_logger
from app.tools import tool_registry
from app.agents.models import (
    AgentState,
    AgentAction,
    AgentStepType,
    AgentResponse,
    AgentConfig,
    AgentObservation,
    ALLOWED_READ_TOOLS,
    SIDE_EFFECT_TOOLS,
    get_tool_descriptions,
)

logger = get_logger(__name__)


class AgentError(Exception):
    """Agent-specific errors."""
    pass


class MaxStepsExceeded(AgentError):
    pass


class ToolErrorLimitExceeded(AgentError):
    pass


class TimeoutExceeded(AgentError):
    pass


class BoundedAgent:
    """
    Bounded agent with strict limits and structured outputs.
    
    The agent operates in a controlled loop:
    1. Analyze request and context
    2. Select legitimate next step (from allowed tools)
    3. Execute controlled read tool
    4. Observe result
    5. Decide next step
    6. Final answer
    
    Safety constraints:
    - MAX_STEPS limit
    - TOOL_ERROR_LIMIT
    - TIMEOUT
    - Only allowed read tools
    - Side-effect tools require policy/workflow authorization
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self._setup_gemini()
    
    def _setup_gemini(self):
        """Initialize Gemini client."""
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            self.config.model_name,
            generation_config={
                "temperature": self.config.temperature,
                "response_mime_type": "application/json",
            }
        )
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with tool descriptions and rules."""
        tool_descs = get_tool_descriptions()
        tools_json = json.dumps(tool_descs, indent=2)
        
        return f"""You are a business resolution agent for Northstar Commerce.
Your job is to investigate customer requests and recommend actions.

AVAILABLE TOOLS (read-only):
{tools_json}

RULES:
1. You can ONLY use the tools listed above. Do not invent tools.
2. You can ONLY call ONE tool per step.
3. You must output structured JSON with the exact schema specified.
4. Side-effect tools (issue_refund, cancel_order, create_escalation) are FORBIDDEN for you to execute directly. They require policy approval and human authorization.
5. Your job is to INVESTIGATE and RECOMMEND, not to execute side effects.
6. If you need information, select the appropriate tool and provide valid parameters.
7. When you have enough evidence to make a recommendation, output step_type "final_answer".

OUTPUT SCHEMA (exact):
{{
  "action": {{
    "step_type": "analyze|select_tool|execute_tool|synthesize|final_answer",
    "reasoning": "string explaining your thought process",
    "tool_name": "string|null (required if step_type is execute_tool)",
    "tool_input": "object|null (required if step_type is execute_tool)",
    "confidence": 0.0-1.0
  }},
  "state_update": {{}}
}}

EXAMPLES:

Investigation start:
{{"action": {{"step_type": "analyze", "reasoning": "User mentions order 10482 delayed. Need to get order details first.", "tool_name": null, "tool_input": null, "confidence": 0.9}}, "state_update": {{"order_id": "10482"}}}}

Tool selection:
{{"action": {{"step_type": "execute_tool", "reasoning": "Need order details to understand status", "tool_name": "get_order", "tool_input": {{"order_id": "10482"}}, "confidence": 0.95}}, "state_update": {{}}}}

Final answer:
{{"action": {{"step_type": "final_answer", "reasoning": "Order 10482 is shipped but delayed. Policy allows refund. Recommending refund of $74.99.", "tool_name": null, "tool_input": null, "confidence": 0.9}}, "state_update": {{"recommendation": "refund", "amount": 74.99}}}}"""

    async def run(self, state: AgentState) -> AgentState:
        """
        Run the bounded agent loop.
        
        Args:
            state: Initial agent state with request_id and user_request
            
        Returns:
            Updated state with final_answer when complete
        """
        start_time = time.time()
        
        while not state.is_complete:
            # Check limits
            if state.steps_taken >= state.max_steps:
                logger.warning(f"Max steps ({state.max_steps}) exceeded for request {state.request_id}")
                state.is_complete = True
                state.final_answer = "Investigation incomplete: maximum steps exceeded"
                break
            
            if state.tool_errors >= state.tool_error_limit:
                logger.warning(f"Tool error limit ({state.tool_error_limit}) exceeded for request {state.request_id}")
                state.is_complete = True
                state.final_answer = "Investigation incomplete: too many tool errors"
                break
            
            if time.time() - start_time > self.config.timeout_seconds:
                logger.warning(f"Timeout ({self.config.timeout_seconds}s) exceeded for request {state.request_id}")
                state.is_complete = True
                state.final_answer = "Investigation incomplete: timeout exceeded"
                break
            
            # Execute one agent step
            state = await self._step(state)
            state.steps_taken += 1
            state.last_step_at = datetime.utcnow()
        
        logger.info(f"Agent completed for request {state.request_id}: steps={state.steps_taken}, complete={state.is_complete}")
        return state
    
    async def _step(self, state: AgentState) -> AgentState:
        """Execute one agent step."""
        # Build context for LLM
        context = self._build_context(state)
        
        # Get action from LLM
        action = await self._get_llm_action(context)
        
        # Validate action
        validated_action = self._validate_action(action, state)
        
        # Execute action
        if validated_action.step_type == AgentStepType.EXECUTE_TOOL:
            state = await self._execute_tool(state, validated_action)
        elif validated_action.step_type == AgentStepType.FINAL_ANSWER:
            state.is_complete = True
            state.final_answer = validated_action.reasoning
            if validated_action.state_update:
                state.context.update(validated_action.state_update)
        elif validated_action.step_type == AgentStepType.ANALYZE:
            if validated_action.state_update:
                state.context.update(validated_action.state_update)
        elif validated_action.step_type == AgentStepType.SYNTHESIZE:
            if validated_action.state_update:
                state.context.update(validated_action.state_update)
        
        return state
    
    def _build_context(self, state: AgentState) -> str:
        """Build context string for LLM."""
        context_parts = [
            f"Request ID: {state.request_id}",
            f"User Request: {state.user_request}",
            f"Order ID: {state.order_id or 'Not yet identified'}",
            f"Intent: {state.intent or 'Not yet classified'}",
            f"Steps Taken: {state.steps_taken}/{state.max_steps}",
            f"Tool Errors: {state.tool_errors}/{state.tool_error_limit}",
        ]
        
        if state.evidence:
            context_parts.append("\nEvidence Collected:")
            for i, ev in enumerate(state.evidence):
                context_parts.append(f"  {i+1}. {ev.get('source', 'unknown')}: {ev.get('content', '')[:200]}")
        
        if state.observations:
            context_parts.append("\nRecent Observations:")
            for obs in state.observations[-3:]:
                status = "SUCCESS" if obs.success else "FAILED"
                context_parts.append(f"  {obs.tool_name}: {status} - {obs.output or obs.error}")
        
        return "\n".join(context_parts)
    
    async def _get_llm_action(self, context: str) -> AgentAction:
        """Get structured action from Gemini."""
        prompt = f"{self._build_system_prompt()}\n\nCONTEXT:\n{context}\n\nOUTPUT:"
        
        try:
            response = await asyncio.wait_for(
                self.model.generate_content_async(prompt),
                timeout=30.0
            )
            
            # Parse JSON response
            action_data = json.loads(response.text)
            return AgentAction(**action_data["action"])
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback: analyze step
            return AgentAction(
                step_type=AgentStepType.ANALYZE,
                reasoning="Failed to parse LLM response, defaulting to analysis",
                confidence=0.1
            )
        except ValidationError as e:
            logger.error(f"Invalid action structure: {e}")
            return AgentAction(
                step_type=AgentStepType.ANALYZE,
                reasoning="Invalid action structure from LLM",
                confidence=0.1
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return AgentAction(
                step_type=AgentStepType.ANALYZE,
                reasoning=f"LLM error: {str(e)}",
                confidence=0.1
            )
    
    def _validate_action(self, action: AgentAction, state: AgentState) -> AgentAction:
        """Validate and sanitize agent action."""
        # If tool execution requested, validate tool
        if action.step_type == AgentStepType.EXECUTE_TOOL:
            if not action.tool_name:
                action.step_type = AgentStepType.ANALYZE
                action.reasoning = "No tool specified for execution"
                return action
            
            # Check if tool is allowed
            if action.tool_name not in ALLOWED_READ_TOOLS:
                logger.warning(f"Agent attempted to use forbidden tool: {action.tool_name}")
                action.step_type = AgentStepType.ANALYZE
                action.reasoning = f"Tool '{action.tool_name}' is not allowed for agent execution"
                return action
            
            # Validate tool input
            tool = tool_registry.get(action.tool_name)
            if tool:
                try:
                    tool.validate_input(action.tool_input or {})
                except ValidationError as e:
                    action.step_type = AgentStepType.ANALYZE
                    action.reasoning = f"Invalid tool input: {e}"
        
        # Check if trying to use side-effect tool
        if action.tool_name in SIDE_EFFECT_TOOLS:
            logger.warning(f"Agent attempted to use side-effect tool: {action.tool_name}")
            action.step_type = AgentStepType.ANALYZE
            action.reasoning = f"Tool '{action.tool_name}' requires policy approval and cannot be executed directly by agent"
        
        return action
    
    async def _execute_tool(self, state: AgentState, action: AgentAction) -> AgentState:
        """Execute the selected tool and record observation."""
        tool_name = action.tool_name
        tool_input = action.tool_input or {}
        
        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
        
        try:
            result: ToolResult = await tool_registry.execute(tool_name, tool_input)
            
            observation = AgentObservation(
                tool_name=tool_name,
                success=result.success,
                output=result.data if result.success else None,
                error=result.error.message if result.error else None
            )
            
            if not result.success:
                state.tool_errors += 1
            
            state.observations.append(observation)
            
            # Store evidence from successful tool calls
            if result.success and result.data:
                evidence_item = {
                    "tool": tool_name,
                    "input": tool_input,
                    "output": result.data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                state.evidence.append(evidence_item)
                
                # Extract order_id from get_order result
                if tool_name == "get_order" and result.data.get("order"):
                    state.order_id = result.data["order"]["order_number"]
                    state.intent = state.intent or "refund_request"  # default intent
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            state.tool_errors += 1
            state.observations.append(AgentObservation(
                tool_name=tool_name,
                success=False,
                error=str(e)
            ))
        
        return state


# Convenience function
async def run_agent(
    request_id: str,
    user_request: str,
    order_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    config: Optional[AgentConfig] = None
) -> AgentState:
    """Run the bounded agent on a user request."""
    initial_state = AgentState(
        request_id=request_id,
        user_request=user_request,
        order_id=order_id,
        customer_id=customer_id,
        max_steps=config.max_steps if config else 10,
        tool_error_limit=config.tool_error_limit if config else 3,
    )
    
    agent = BoundedAgent(config)
    return await agent.run(initial_state)