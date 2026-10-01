from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RetrievalStrategy(str, Enum):
    SEMANTIC = "semantic"
    LEXICAL = "lexical"
    HYBRID = "hybrid"


class Evidence(BaseModel):
    """Structured evidence object for citation traceability."""
    chunk_id: str
    document_id: str
    document_name: str
    section: str
    source: str
    version: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any] = {}
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC
    filter_metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    query: str
    evidence: List[Evidence]
    total_candidates: int
    retrieval_strategy: RetrievalStrategy
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SearchCompanyPolicyRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchCompanyPolicyResponse(BaseModel):
    results: List[Evidence] = []
    error: Optional[str] = None