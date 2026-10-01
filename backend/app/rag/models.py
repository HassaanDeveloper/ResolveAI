from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class DocumentSource(str, Enum):
    INTERNAL_POLICY = "internal-policy"
    INTERNAL_SOP = "internal-sop"
    TEST_POLICY = "test-policy"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChunkingStrategy(str, Enum):
    SEMANTIC = "semantic"
    FIXED_SIZE = "fixed_size"
    MARKDOWN_HEADERS = "markdown_headers"


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source: DocumentSource
    version: str
    content: str
    metadata: Dict[str, Any] = {}
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error: Optional[str] = None


class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    chunk_index: int
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngestionRequest(BaseModel):
    file_path: str
    document_name: str
    source: DocumentSource
    version: str
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.MARKDOWN_HEADERS
    metadata: Dict[str, Any] = {}


class IngestionResult(BaseModel):
    success: bool
    document_id: Optional[str] = None
    chunks_created: int = 0
    embeddings_stored: int = 0
    error: Optional[str] = None
    processing_time_ms: int = 0


class SearchQuery(BaseModel):
    query: str
    max_results: int = 5
    similarity_threshold: float = 0.7
    filter_metadata: Dict[str, Any] = {}


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    section: str
    content: str
    source: str
    version: str
    relevance_score: float
    metadata: Dict[str, Any] = {}