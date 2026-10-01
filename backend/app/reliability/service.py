import asyncio
import random
import time
from typing import Optional, Callable, TypeVar, Any, Dict
from functools import wraps

from app.services.database import get_supabase_client
from app.reliability.models import (
    OperationStatus,
    IdempotencyKey,
    RetryPolicy,
    OperationResult,
    TimeoutConfig,
    DEFAULT_READ_RETRY,
    DEFAULT_WRITE_RETRY,
)
from app.core.logging import get_logger
from app.core.exceptions import ValidationError, ResolveAIException

logger = get_logger(__name__)

T = TypeVar('T')


class IdempotencyService:
    """Service for managing idempotency keys and preventing duplicate operations."""
    
    def __init__(self):
        self.supabase = None
    
    def _get_client(self):
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase
    
    def _stringify_error(self, stored_error: Any) -> str:
        """
        Normalise a stored operation error into a string.

        `operations.result.error` is not schema-constrained: mark_failed stores the
        raw driver error, which for Postgres is a dict
        (`{"code": "23505", "details": ..., "message": ...}`). Passing that dict
        straight into `OperationResult.error` (a str) raised a pydantic
        ValidationError inside check_idempotency, which the calling tool could only
        report as a generic internal error.
        """
        if stored_error is None:
            return "Operation previously failed"
        if isinstance(stored_error, str):
            return stored_error or "Operation previously failed"
        if isinstance(stored_error, dict):
            for key in ("message", "details", "error"):
                value = stored_error.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            return str(stored_error)
        return str(stored_error)

    async def check_idempotency(self, operation_id: str) -> Optional[OperationResult]:
        """
        Check if an operation has already been executed.
        
        Returns:
            OperationResult if found, None if not found
        """
        client = self._get_client()
        
        result = client.table("operations").select("*").eq("operation_id", operation_id).execute()
        
        if not result.data:
            return None
        
        op = result.data[0]
        
        if op["status"] == OperationStatus.EXECUTED.value:
            return OperationResult(
                success=True,
                data=op.get("result"),
                idempotent=True,
                retry_count=0
            )
        elif op["status"] == OperationStatus.FAILED.value:
            stored_result = op.get("result") or {}
            raw_error = stored_result.get("error") if isinstance(stored_result, dict) else None
            return OperationResult(
                success=False,
                error=self._stringify_error(raw_error),
                idempotent=True
            )
        elif op["status"] in [OperationStatus.PENDING.value, OperationStatus.EXECUTING.value]:
            return OperationResult(
                success=False,
                error=f"Operation {operation_id} is already in progress",
                idempotent=True
            )
        
        return None
    
    async def reserve_operation(self, operation_id: str, operation_type: str) -> bool:
        """
        Reserve an operation ID for execution.
        
        Returns True if reservation successful, False if already exists.
        """
        client = self._get_client()
        
        try:
            result = client.table("operations").insert({
                "operation_id": operation_id,
                "operation_type": operation_type,
                "status": OperationStatus.PENDING.value,
                "result": None
            }).execute()
            
            return bool(result.data)
        except Exception as e:
            # Check if it's a duplicate key error
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                return False
            raise
    
    async def mark_executing(self, operation_id: str) -> None:
        """Mark operation as currently executing."""
        client = self._get_client()
        client.table("operations").update({
            "status": OperationStatus.EXECUTING.value,
            "updated_at": "now()"
        }).eq("operation_id", operation_id).execute()
    
    async def mark_executed(self, operation_id: str, result: Dict[str, Any]) -> None:
        """Mark operation as successfully executed with result."""
        client = self._get_client()
        client.table("operations").update({
            "status": OperationStatus.EXECUTED.value,
            "result": result,
            "updated_at": "now()",
            "completed_at": "now()"
        }).eq("operation_id", operation_id).execute()
    
    async def mark_failed(self, operation_id: str, error: str) -> None:
        """Mark operation as failed."""
        client = self._get_client()
        client.table("operations").update({
            "status": OperationStatus.FAILED.value,
            "result": {"error": error},
            "updated_at": "now()"
        }).eq("operation_id", operation_id).execute()
    
    async def mark_duplicate(self, operation_id: str) -> None:
        """Mark operation as duplicate."""
        client = self._get_client()
        client.table("operations").update({
            "status": OperationStatus.DUPLICATE.value,
            "updated_at": "now()"
        }).eq("operation_id", operation_id).execute()

    async def reset_operation(self, operation_id: str) -> bool:
        """
        Clear a stale FAILED ledger entry back to PENDING so the same
        operation_id can be re-attempted.

        This reuses the existing ledger row (the operation_id unique constraint is
        untouched) instead of inserting a second one.

        Returns True if a row existed and was reset, False otherwise.
        """
        client = self._get_client()
        existing = client.table("operations").select("operation_id").eq("operation_id", operation_id).execute()
        if not existing.data:
            return False
        client.table("operations").update({
            "status": OperationStatus.PENDING.value,
            "result": None,
            "updated_at": "now()"
        }).eq("operation_id", operation_id).execute()
        return True


idempotency_service = IdempotencyService()


# =============================================
# Retry Logic
# =============================================

async def with_retry(
    func: Callable[..., T],
    policy: RetryPolicy = DEFAULT_READ_RETRY,
    operation_name: str = "operation",
    *args,
    **kwargs
) -> T:
    """
    Execute a function with retry logic.
    
    Args:
        func: Async function to execute
        policy: Retry policy configuration
        operation_name: Name for logging
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Result of func
        
    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None
    
    for attempt in range(1, policy.max_attempts + 1):
        try:
            logger.debug(f"Executing {operation_name}, attempt {attempt}/{policy.max_attempts}")
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt == policy.max_attempts:
                logger.error(f"{operation_name} failed after {policy.max_attempts} attempts: {e}")
                raise
            
            # Calculate delay with exponential backoff and optional jitter
            delay = min(
                policy.base_delay_seconds * (policy.exponential_base ** (attempt - 1)),
                policy.max_delay_seconds
            )
            
            if policy.jitter:
                delay *= (0.5 + random.random() * 0.5)  # 0.5-1.0 jitter
            
            logger.warning(f"{operation_name} attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
            await asyncio.sleep(delay)
    
    # Should not reach here
    raise last_exception


def with_timeout(
    timeout_config: TimeoutConfig = TimeoutConfig(),
    operation_name: str = "operation"
):
    """
    Decorator to add timeout to an async function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_config.total_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"{operation_name} timed out after {timeout_config.total_timeout}s")
                raise TimeoutError(f"{operation_name} timed out after {timeout_config.total_timeout}s")
        return wrapper
    return decorator


class CircuitBreaker:
    """Simple circuit breaker for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open
        self._half_open_calls = 0
    
    @property
    def state(self) -> str:
        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure_time and time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = "half-open"
                self._half_open_calls = 0
        return self._state
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        if self.state == "open":
            raise ResolveAIException("Circuit breaker is open", error_code="CIRCUIT_BREAKER_OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self._failure_count = 0
        self._state = "closed"
        self._half_open_calls = 0
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == "half-open":
            self._state = "open"
        elif self._failure_count >= self.failure_threshold:
            self._state = "open"


# Default circuit breakers for external services
supabase_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
gemini_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)