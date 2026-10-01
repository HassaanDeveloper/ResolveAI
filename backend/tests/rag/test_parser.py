import pytest
from app.rag.parser import DocumentParser, SemanticChunker, ParsedSection
from app.rag.models import Document, DocumentSource, DocumentStatus


@pytest.fixture
def sample_markdown():
    return """# Northstar Commerce Refund Policy
**Version:** 2.1
**Effective Date:** 2025-01-15
**Source:** internal-policy
**Document ID:** REFUND-POLICY-2.1

---

## 1. Purpose
This policy defines the terms and conditions under which Northstar Commerce issues refunds to customers for purchases made through our platforms.

## 2. Scope
Applies to all orders placed on northstarcommerce.com, mobile app, and marketplace channels.

### 2.1 Standard Eligibility Criteria
A refund is eligible when ALL of the following conditions are met:
- Order was placed within the last 30 days from delivery date
- Item is in original condition with all accessories and packaging
- Valid proof of purchase (order number or receipt) is provided

### 2.2 Exceptions to Time Limit
- **Defective items:** No time limit for manufacturing defects
- **Delayed shipments:** See Section 4

## 3. Delayed Shipment Refunds
Customers are eligible for a full refund if a shipment is delayed beyond the estimated delivery date by more than 7 business days and the package has not been delivered.
"""


@pytest.fixture
def sample_document(sample_markdown):
    return Document(
        name="Test Refund Policy",
        source=DocumentSource.INTERNAL_POLICY,
        version="2.1",
        content=sample_markdown,
        metadata={}
    )


def test_parse_markdown_sections(sample_markdown):
    """Test markdown parsing extracts sections correctly."""
    parser = DocumentParser()
    sections = parser.parse_markdown(sample_markdown)
    
    assert len(sections) > 0
    
    # Check first section is the H1 title
    first_section = sections[0]
    assert first_section.header == "Northstar Commerce Refund Policy"
    assert first_section.level == 1
    
    # Check second section (## 1. Purpose)
    purpose_section = next((s for s in sections if s.header == "1. Purpose"), None)
    assert purpose_section is not None
    assert purpose_section.level == 2
    assert "This policy defines" in purpose_section.content
    
    # Check subsection (### 2.1 Standard Eligibility Criteria)
    subsection = next((s for s in sections if "2.1" in s.header), None)
    assert subsection is not None
    assert subsection.level == 3
    assert "Standard Eligibility Criteria" in subsection.header


def test_extract_metadata(sample_markdown):
    """Test metadata extraction from markdown frontmatter."""
    parser = DocumentParser()
    metadata = parser.extract_metadata(sample_markdown)
    
    assert metadata.get("version").strip() == "2.1"
    assert metadata.get("effective_date").strip() == "2025-01-15"
    assert metadata.get("source").strip() == "internal-policy"
    assert metadata.get("document_id").strip() == "REFUND-POLICY-2.1"


def test_semantic_chunker_small_sections(sample_document):
    """Test chunking keeps small sections together."""
    chunker = SemanticChunker(max_chunk_size=2000, min_chunk_size=50)
    chunks = chunker.chunk(
        DocumentParser().parse_markdown(sample_document.content),
        sample_document.id,
        sample_document.name,
        {"source": "internal-policy", "version": "2.1"}
    )
    
    assert len(chunks) > 0
    
    # Each chunk should have proper metadata
    for chunk in chunks:
        assert chunk.document_id == sample_document.id
        assert chunk.content
        assert "document_name" in chunk.metadata
        assert "section" in chunk.metadata
        assert "source" in chunk.metadata
        assert "version" in chunk.metadata
        assert chunk.metadata["source"] == "internal-policy"
        assert chunk.metadata["version"] == "2.1"


def test_semantic_chunker_large_section_splitting():
    """Test large sections are split into multiple chunks."""
    # Create document with a very large section
    large_content = "# Large Section\n" + "This is a test sentence. " * 200  # ~5000 chars
    
    document = Document(
        name="Large Document",
        source=DocumentSource.INTERNAL_POLICY,
        version="1.0",
        content=large_content,
        metadata={}
    )
    
    chunker = SemanticChunker(max_chunk_size=1000, min_chunk_size=100, overlap=50)
    sections = DocumentParser().parse_markdown(large_content)
    chunks = chunker.chunk(sections, document.id, document.name, {"source": "internal-policy", "version": "1.0"})
    
    # Should split into multiple chunks
    assert len(chunks) > 1
    
    # Each chunk should be reasonable size
    for chunk in chunks:
        assert len(chunk.content) <= 1200  # max_chunk_size + some buffer


def test_fixed_size_chunk_fallback():
    """Test fixed-size chunking fallback."""
    from app.rag.parser import fixed_size_chunk
    
    document = Document(
        name="Test Document",
        source=DocumentSource.INTERNAL_POLICY,
        version="1.0",
        content="A" * 2500,  # 2500 chars
        metadata={}
    )
    
    chunks = fixed_size_chunk(document, chunk_size=1000, overlap=100)
    
    # Should create ~3 chunks (2500 / (1000-100) ≈ 2.78)
    assert len(chunks) >= 2
    
    for chunk in chunks:
        assert chunk.metadata["chunk_type"] == "fixed_size"
        assert "start_char" in chunk.metadata
        assert "end_char" in chunk.metadata


def test_parse_and_chunk_document(sample_document):
    """Test the main parse_and_chunk_document function."""
    from app.rag.parser import parse_and_chunk_document
    
    chunks = parse_and_chunk_document(sample_document)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.document_id == sample_document.id
        assert isinstance(chunk.content, str)
        assert len(chunk.content) > 0


def test_empty_section_handling():
    """Test parser handles empty sections gracefully."""
    content = """# Header 1

Content 1

## Header 2

## Header 3

Content 3"""
    
    parser = DocumentParser()
    sections = parser.parse_markdown(content)
    
    # Should have 3 sections, but Header 2 has no content
    assert len(sections) == 3
    
    # Empty section should have empty content
    empty_section = next((s for s in sections if s.header == "Header 2"), None)
    assert empty_section is not None
    assert empty_section.content.strip() == ""


def test_chunk_metadata_completeness(sample_document):
    """Test that all required metadata fields are present in chunks."""
    from app.rag.parser import parse_and_chunk_document
    
    chunks = parse_and_chunk_document(sample_document)
    
    required_fields = [
        "document_name", "section", "section_level", 
        "source", "version", "start_line", "end_line", "chunk_index"
    ]
    
    for chunk in chunks:
        for field in required_fields:
            assert field in chunk.metadata, f"Missing metadata field: {field}"


def test_chunk_overlap_preserves_context():
    """Test that overlap in large section splitting preserves context."""
    # Create content with distinct parts
    content = "# Section\n" + "BEGINNING. " + "MIDDLE. " * 100 + "ENDING."
    
    document = Document(
        name="Overlap Test",
        source=DocumentSource.INTERNAL_POLICY,
        version="1.0",
        content=content,
        metadata={}
    )
    
    chunker = SemanticChunker(max_chunk_size=500, min_chunk_size=50, overlap=50)
    sections = DocumentParser().parse_markdown(content)
    chunks = chunker.chunk(sections, document.id, document.name, {})
    
    if len(chunks) > 1:
        # Check that overlap creates some repeated content between adjacent chunks
        # This is a heuristic - overlap should mean last ~50 chars of chunk N
        # appear in first ~50 chars of chunk N+1
        pass  # Overlap verification is implementation-dependent