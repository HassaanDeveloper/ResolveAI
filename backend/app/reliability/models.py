from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, TypeVar, Generic
from datetime import datetime


T = TypeVar('T')


class OperationStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 5.0
    exponential_base: float = 2.0
    jitter: bool = True


class IdempotencyKey(BaseModel):
    key: str
    operation_type: str
    status: OperationStatus = OperationStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class OperationResult(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    idempotent: bool = False
    retry_count: int = 0


class TimeoutConfig(BaseModel):
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0


# Default retry policies
DEFAULT_READ_RETRY = RetryPolicy(max_attempts=3, base_delay_seconds=0.5, max_delay_seconds=5.0)
DEFAULT_WRITE_RETRY = RetryPolicy(max_attempts=1, base_delay_seconds=0.0, max_delay_seconds=0.0)  # No retries for writes by default