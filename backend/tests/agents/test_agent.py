import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.models import (
    AgentState,
    AgentAction,
    AgentStepType,
    AgentConfig,
    ALLOWED_READ_TOOLS,
)
from app.agents.core import (
    BoundedAgent,
    run_agent,
    MaxStepsExceeded,
    ToolErrorLimitExceeded,
    TimeoutExceeded,
)


@pytest.fixture
def mock_gemini_model():
    """Mock the Gemini model."""
    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        with patch("app.core.config.settings.GEMINI_API_KEY", "test-key"):
            mock_model = MagicMock()
            mock_model_class.return_value = mock_model
            yield mock_model


@pytest.fixture
def agent_config():
    return AgentConfig(
        max_steps=5,
        tool_error_limit=2,
        timeout_seconds=10,
        temperature=0.0,
    )


@pytest.fixture
def sample_state():
    return AgentState(
        request_id="req-test-123",
        user_request="Order 10482 hasn't arrived and I want a refund",
        order_id=None,
        max_steps=5,
        tool_error_limit=2,
    )


class TestBoundedAgent:
    """Test the bounded agent core logic."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_gemini_model, agent_config):
        """Test agent initializes with config."""
        agent = BoundedAgent(agent_config)
        assert agent.config.max_steps == 5
        assert agent.config.tool_error_limit == 2
        assert agent.config.timeout_seconds == 10

    @pytest.mark.asyncio
    async def test_agent_requires_api_key(self):
        """Test agent fails without API key."""
        with patch("app.core.config.settings.GEMINI_API_KEY", "your-gemini-api-key-here"):
            with pytest.raises(ValueError, match="GEMINI_API_KEY not configured"):
                BoundedAgent()

    @pytest.mark.asyncio
    async def test_max_steps_exceeded(self, mock_gemini_model, agent_config):
        """Test agent stops when max steps exceeded."""
        # Mock LLM to always return analyze step
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "action": {
                "step_type": "analyze",
                "reasoning": "Keep analyzing",
                "tool_name": None,
                "tool_input": None,
                "confidence": 0.5,
                "state_update": {}
            },
            "state_update": {}
        })
        mock_gemini_model.generate_content_async = AsyncMock(return_value=mock_response)

        agent = BoundedAgent(agent_config)

        state = AgentState(
            request_id="req-1",
            user_request="Test request",
            max_steps=2,
            tool_error_limit=3,
        )

        result = await agent.run(state)

        assert result.steps_taken == 2
        assert result.is_complete is True
        assert "maximum steps exceeded" in result.final_answer.lower()

    @pytest.mark.asyncio
    async def test_tool_error_limit_exceeded(self, mock_gemini_model, agent_config):
        """Test agent stops when tool error limit exceeded."""
        # Mock LLM to request tool execution
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "action": {
                "step_type": "execute_tool",
                "reasoning": "Need order details",
                "tool_name": "get_order",
                "tool_input": {"order_id": "10482"},
                "confidence": 0.9,
                "state_update": {}
            },
            "state_update": {}
        })
        mock_gemini_model.generate_content_async = AsyncMock(return_value=mock_response)

        # Mock tool registry to always fail
        with patch("app.agents.core.tool_registry") as mock_registry:
            mock_registry.execute = AsyncMock(return_value=MagicMock(
                success=False,
                error=MagicMock(message="Tool failed"),
                data=None
            ))

            agent = BoundedAgent(agent_config)

            state = AgentState(
                request_id="req-1",
                user_request="Test request",
                max_steps=10,
                tool_error_limit=2,
            )

            result = await agent.run(state)

            assert result.tool_errors >= 2
            assert result.is_complete is True
            assert "tool errors" in result.final_answer.lower()

    @pytest.mark.asyncio
    async def test_forbidden_tool_rejected(self, mock_gemini_model, agent_config):
        """Test agent cannot execute side-effect tools."""
        # Mock LLM to request side-effect tool
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "action": {
                "step_type": "execute_tool",
                "reasoning": "Issue refund directly",
                "tool_name": "issue_refund",
                "tool_input": {"order_id": "10482", "amount": 74.99, "operation_id": "test-123"},
                "confidence": 0.9,
                "state_update": {}
            },
            "state_update": {}
        })
        mock_gemini_model.generate_content_async = AsyncMock(return_value=mock_response)

        agent = BoundedAgent(agent_config)

        state = AgentState(
            request_id="req-1",
            user_request="Refund order 10482",
            max_steps=5,
            tool_error_limit=3,
        )

        result = await agent.run(state)

        # Should have rejected the forbidden tool
        assert result.tool_errors == 0  # Not a tool error, just rejected
        # Should have fallen back to analyze
        assert len(result.observations) == 0


class TestRunAgentFunction:
    """Test the run_agent convenience function."""

    @pytest.mark.asyncio
    async def test_run_agent_creates_initial_state(self, mock_gemini_model):
        """Test run_agent creates proper initial state."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "action": {
                "step_type": "final_answer",
                "reasoning": "Test complete",
                "tool_name": None,
                "tool_input": None,
                "confidence": 1.0,
                "state_update": {}
            },
            "state_update": {}
        })
        mock_gemini_model.generate_content_async = AsyncMock(return_value=mock_response)

        state = await run_agent(
            request_id="req-123",
            user_request="Test request",
            order_id="10482",
            customer_id="CUST-001",
        )

        assert state.request_id == "req-123"
        assert state.user_request == "Test request"
        assert state.order_id == "10482"
        assert state.customer_id == "CUST-001"
        assert state.is_complete is True
        assert state.final_answer == "Test complete"


class TestAgentModels:
    """Test agent data models."""

    def test_agent_action_validation(self):
        """Test AgentAction validates step types."""
        action = AgentAction(
            step_type=AgentStepType.ANALYZE,
            reasoning="Test",
            confidence=0.9
        )
        assert action.step_type == AgentStepType.ANALYZE

    def test_agent_action_confidence_bounds(self):
        """Test confidence must be 0-1."""
        with pytest.raises(ValueError):
            AgentAction(step_type=AgentStepType.ANALYZE, reasoning="Test", confidence=1.5)

        with pytest.raises(ValueError):
            AgentAction(step_type=AgentStepType.ANALYZE, reasoning="Test", confidence=-0.1)

    def test_allowed_read_tools(self):
        """Test allowed tools list."""
        assert "get_order" in ALLOWED_READ_TOOLS
        assert "get_customer" in ALLOWED_READ_TOOLS
        assert "get_shipping_status" in ALLOWED_READ_TOOLS
        assert "search_company_policy" in ALLOWED_READ_TOOLS
        assert "calculate_refund" in ALLOWED_READ_TOOLS
        assert "issue_refund" not in ALLOWED_READ_TOOLS
        assert "cancel_order" not in ALLOWED_READ_TOOLS

    def test_agent_config_defaults(self):
        """Test AgentConfig defaults."""
        config = AgentConfig()
        assert config.max_steps == 10
        assert config.tool_error_limit == 3
        assert config.timeout_seconds == 60
        assert config.temperature == 0.1