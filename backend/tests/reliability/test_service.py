import pytest
import asyncio
import random
from unittest.mock import AsyncMock, MagicMock, patch
from app.reliability.models import (
    OperationStatus,
    RetryPolicy,
    IdempotencyKey,
    OperationResult,
    TimeoutConfig,
    DEFAULT_READ_RETRY,
    DEFAULT_WRITE_RETRY,
)
from app.reliability.service import (
    IdempotencyService,
    idempotency_service,
    with_retry,
    with_timeout,
    CircuitBreaker,
    supabase_circuit_breaker,
    gemini_circuit_breaker,
)


@pytest.fixture
def mock_supabase():
    with patch("app.reliability.service.get_supabase_client") as mock_get:
        client = MagicMock()
        mock_get.return_value = client
        yield client


@pytest.fixture
def sample_operation_id():
    return "test-operation-123"


class TestIdempotencyService:
    """Test the idempotency service."""

    @pytest.mark.asyncio
    async def test_check_idempotency_not_found(self, mock_supabase):
        """Test checking idempotency for non-existent operation."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

        service = IdempotencyService()
        result = await service.check_idempotency("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_check_idempotency_executed(self, mock_supabase):
        """Test checking idempotency for already executed operation."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "operation_id": "test-op-1",
            "status": "executed",
            "result": {"refund_id": "refund-123", "currency": "USD", "processed_at": "2025-01-01T00:00:00+00:00"}
        }]

        service = IdempotencyService()
        result = await service.check_idempotency("test-op-1")

        assert result is not None
        assert result.success is True
        assert result.idempotent is True
        assert result.data["refund_id"] == "refund-123"

    @pytest.mark.asyncio
    async def test_check_idempotency_failed(self, mock_supabase):
        """Test checking idempotency for failed operation."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "operation_id": "test-op-2",
            "status": "failed",
            "result": {"error": "Payment processor timeout"}
        }]

        service = IdempotencyService()
        result = await service.check_idempotency("test-op-2")

        assert result is not None
        assert result.success is False
        assert result.idempotent is True
        assert "Payment processor timeout" in result.error

    @pytest.mark.asyncio
    async def test_check_idempotency_failed_structured_error(self, mock_supabase):
        """
        A stored failure can be a structured driver error dict (e.g. Postgres
        23505). OperationResult.error is typed as str, so this must be normalised
        instead of raising a pydantic ValidationError.
        """
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "operation_id": "test-op-2b",
            "status": "failed",
            "result": {
                "error": {
                    "code": "23505",
                    "details": 'Key (operation_id)=(refund-order-10482-74.99) already exists.',
                    "hint": None,
                    "message": 'duplicate key value violates unique constraint "refunds_operation_id_key"',
                },
                "message": "Insert failed: duplicate key",
            }
        }]

        service = IdempotencyService()
        result = await service.check_idempotency("test-op-2b")

        assert result is not None
        assert result.success is False
        assert result.idempotent is True
        assert isinstance(result.error, str)
        assert "refunds_operation_id_key" in result.error

    @pytest.mark.asyncio
    async def test_check_idempotency_in_progress(self, mock_supabase):
        """Test checking idempotency for operation in progress."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "operation_id": "test-op-3",
            "status": "executing",
            "result": None
        }]

        service = IdempotencyService()
        result = await service.check_idempotency("test-op-3")

        assert result is not None
        assert result.success is False
        assert result.idempotent is True
        assert "already in progress" in result.error

    @pytest.mark.asyncio
    async def test_reserve_operation_success(self, mock_supabase):
        """Test successful operation reservation."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"operation_id": "new-op-1"}]

        service = IdempotencyService()
        result = await service.reserve_operation("new-op-1", "issue_refund")

        assert result is True

    @pytest.mark.asyncio
    async def test_reserve_operation_duplicate(self, mock_supabase):
        """Test reservation failure for duplicate."""
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("duplicate key value violates unique constraint")

        service = IdempotencyService()
        result = await service.reserve_operation("existing-op", "issue_refund")

        assert result is False

    @pytest.mark.asyncio
    async def test_mark_executed(self, mock_supabase):
        """Test marking operation as executed."""
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        service = IdempotencyService()
        await service.mark_executed("test-op", {"refund_id": "ref-123"})

        # Verify update was called
        mock_supabase.table.return_value.update.assert_called()

    @pytest.mark.asyncio
    async def test_mark_failed(self, mock_supabase):
        """Test marking operation as failed."""
        service = IdempotencyService()
        await service.mark_failed("test-op", "Test error")

        mock_supabase.table.return_value.update.assert_called()


class TestRetryLogic:
    """Test retry logic."""

    @pytest.mark.asyncio
    async def test_with_retry_success_first_attempt(self):
        """Test retry succeeds on first attempt."""
        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await with_retry(success_func, policy=RetryPolicy(max_attempts=3))
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_with_retry_success_after_failures(self):
        """Test retry succeeds after some failures."""
        call_count = 0

        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        policy = RetryPolicy(max_attempts=5, base_delay_seconds=0.01)
        result = await with_retry(eventually_succeeds, policy=policy)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_with_retry_exhausted(self):
        """Test retry exhausts all attempts."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent failure")

        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.01)
        
        with pytest.raises(Exception, match="Permanent failure"):
            await with_retry(always_fails, policy=policy)
        
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_with_timeout_decorator(self):
        """Test timeout decorator."""
        @with_timeout(TimeoutConfig(total_timeout=0.1))
        async def slow_operation():
            await asyncio.sleep(1)
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await slow_operation()


class TestCircuitBreaker:
    """Test circuit breaker."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_by_default(self):
        """Test circuit breaker starts closed."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def success():
            return "ok"
        
        result = await breaker.call(success)
        assert result == "ok"
        assert breaker.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        async def fail():
            raise Exception("Service down")
        
        # First failure
        with pytest.raises(Exception):
            await breaker.call(fail)
        
        # Second failure - should open
        with pytest.raises(Exception):
            await breaker.call(fail)
        
        assert breaker.state == "open"
        
        # Third call should be rejected by circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await breaker.call(lambda: "success")

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker goes half-open after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        
        async def fail():
            raise Exception("Service down")
        
        async def success():
            return "ok"
        
        # Trigger failure
        with pytest.raises(Exception):
            await breaker.call(fail)
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(0.02)
        
        # Should be half-open now
        assert breaker.state == "half-open"
        
        # Success should close it
        result = await breaker.call(success)
        assert result == "ok"
        assert breaker.state == "closed"


class TestDefaultPolicies:
    """Test default retry policies."""

    def test_default_read_retry(self):
        """Test default read retry policy."""
        assert DEFAULT_READ_RETRY.max_attempts == 3
        assert DEFAULT_READ_RETRY.base_delay_seconds == 0.5
        assert DEFAULT_READ_RETRY.max_delay_seconds == 5.0
        assert DEFAULT_READ_RETRY.exponential_base == 2.0

    def test_default_write_retry(self):
        """Test default write retry policy (no retries)."""
        assert DEFAULT_WRITE_RETRY.max_attempts == 1
        assert DEFAULT_WRITE_RETRY.base_delay_seconds == 0.0

    def test_timeout_config_defaults(self):
        """Test timeout config defaults."""
        config = TimeoutConfig()
        assert config.connect_timeout == 10.0
        assert config.read_timeout == 30.0
        assert config.total_timeout == 60.0


class TestModels:
    """Test reliability models."""

    def test_operation_status_enum(self):
        """Test OperationStatus enum values."""
        assert OperationStatus.PENDING == "pending"
        assert OperationStatus.EXECUTING == "executing"
        assert OperationStatus.EXECUTED == "executed"
        assert OperationStatus.FAILED == "failed"
        assert OperationStatus.DUPLICATE == "duplicate"

    def test_operation_result(self):
        """Test OperationResult model."""
        result = OperationResult(success=True, data={"key": "value"}, idempotent=True)
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.idempotent is True
        assert result.retry_count == 0

    def test_retry_policy(self):
        """Test RetryPolicy model."""
        policy = RetryPolicy(max_attempts=5, base_delay_seconds=1.0)
        assert policy.max_attempts == 5
        assert policy.base_delay_seconds == 1.0