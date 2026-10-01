import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from app.rag.models import Document, DocumentChunk, ChunkingStrategy


@dataclass
class ParsedSection:
    header: str
    level: int
    content: str
    start_line: int
    end_line: int


class DocumentParser:
    """Parse markdown documents into structured sections."""
    
    @staticmethod
    def parse_markdown(content: str) -> List[ParsedSection]:
        """
        Parse markdown content into sections based on headers.
        Returns list of sections with header, level, content, and line numbers.
        """
        lines = content.split('\n')
        sections = []
        current_section = None
        
        for i, line in enumerate(lines):
            # Match markdown headers (# ## ### etc.)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # Save previous section
                if current_section:
                    current_section.end_line = i - 1
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                header = header_match.group(2).strip()
                current_section = ParsedSection(
                    header=header,
                    level=level,
                    content="",
                    start_line=i,
                    end_line=len(lines) - 1
                )
            elif current_section:
                current_section.content += line + "\n"
        
        # Don't forget the last section
        if current_section:
            sections.append(current_section)
        
        # If no markdown headers found, treat entire content as a single section
        if not sections:
            sections.append(ParsedSection(
                header="Document",
                level=1,
                content=content.strip(),
                start_line=0,
                end_line=len(lines) - 1
            ))
        
        # Clean up content
        for section in sections:
            section.content = section.content.strip()
        
        return sections

    @staticmethod
    def extract_metadata(content: str) -> Dict[str, Any]:
        """Extract document metadata from frontmatter or header comments."""
        metadata = {}
        
        # Try to extract from first few lines (version, date, source, etc.)
        lines = content.split('\n')[:20]
        for line in lines:
            line = line.strip()
            if line.startswith('**Version:**') or line.startswith('Version:'):
                metadata['version'] = line.split(':', 1)[1].strip().strip('*')
            elif line.startswith('**Effective Date:**') or line.startswith('Effective Date:'):
                metadata['effective_date'] = line.split(':', 1)[1].strip().strip('*')
            elif line.startswith('**Source:**') or line.startswith('Source:'):
                metadata['source'] = line.split(':', 1)[1].strip().strip('*')
            elif line.startswith('**Document ID:**') or line.startswith('Document ID:'):
                metadata['document_id'] = line.split(':', 1)[1].strip().strip('*')
        
        return metadata


class SemanticChunker:
    """
    Semantic/structure-aware chunking that preserves document hierarchy.
    Chunks by markdown headers, keeping related content together.
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        overlap: int = 50
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
    
    def chunk(self, sections: List[ParsedSection], document_id: str, document_name: str, document_metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Convert parsed sections into chunks.
        Each section becomes a chunk, with large sections split further.
        """
        chunks = []
        chunk_index = 0
        
        for section in sections:
            if not section.content.strip():
                continue
            
            # If section is small enough, keep as single chunk
            if len(section.content) <= self.max_chunk_size:
                chunk = self._create_chunk(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    content=section.content,
                    section_header=section.header,
                    section_level=section.level,
                    document_name=document_name,
                    document_metadata=document_metadata,
                    start_line=section.start_line,
                    end_line=section.end_line
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Split large section into multiple chunks
                sub_chunks = self._split_large_section(
                    section.content,
                    document_id,
                    chunk_index,
                    section.header,
                    section.level,
                    document_name,
                    document_metadata,
                    section.start_line,
                    section.end_line
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
        
        return chunks
    
    def _create_chunk(
        self,
        document_id: str,
        chunk_index: int,
        content: str,
        section_header: str,
        section_level: int,
        document_name: str,
        document_metadata: Dict[str, Any],
        start_line: int,
        end_line: int
    ) -> DocumentChunk:
        """Create a single chunk with metadata."""
        metadata = {
            "document_name": document_name,
            "section": section_header,
            "section_level": section_level,
            "source": document_metadata.get("source", "unknown"),
            "version": document_metadata.get("version", "unknown"),
            "start_line": start_line,
            "end_line": end_line,
            "chunk_index": chunk_index,
        }
        # Add any additional document metadata
        for key, value in document_metadata.items():
            if key not in metadata:
                metadata[key] = value
        
        return DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content.strip(),
            metadata=metadata
        )
    
    def _split_large_section(
        self,
        content: str,
        document_id: str,
        start_chunk_index: int,
        section_header: str,
        section_level: int,
        document_name: str,
        document_metadata: Dict[str, Any],
        start_line: int,
        end_line: int
    ) -> List[DocumentChunk]:
        """Split large content into overlapping chunks."""
        chunks = []
        words = content.split()
        chunk_index = start_chunk_index
        
        # Calculate approximate word counts
        words_per_chunk = self.max_chunk_size // 5  # ~5 chars per word
        overlap_words = self.overlap // 5
        
        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_content = " ".join(chunk_words)
            
            if len(chunk_content) < self.min_chunk_size and i > 0:
                # Too small, merge with previous
                continue
            
            chunk = self._create_chunk(
                document_id=document_id,
                chunk_index=chunk_index,
                content=chunk_content,
                section_header=f"{section_header} (part {chunk_index - start_chunk_index + 1})",
                section_level=section_level,
                document_name=document_name,
                document_metadata=document_metadata,
                start_line=start_line,
                end_line=end_line
            )
            chunks.append(chunk)
            chunk_index += 1
            
            if i + words_per_chunk >= len(words):
                break
        
        return chunks


def parse_and_chunk_document(document: Document) -> List[DocumentChunk]:
    """Main entry point: parse document and create chunks based on strategy."""
    parser = DocumentParser()
    sections = parser.parse_markdown(document.content)
    
    # Extract metadata from document
    doc_metadata = DocumentParser.extract_metadata(document.content)
    doc_metadata.update(document.metadata)
    
    # Choose chunker based on strategy
    if document.metadata.get("chunking_strategy") == ChunkingStrategy.FIXED_SIZE:
        # Fallback to simple fixed-size chunking
        return fixed_size_chunk(document)
    else:
        # Default: semantic/markdown-aware chunking
        chunker = SemanticChunker()
        return chunker.chunk(sections, document.id, document.name, doc_metadata)


def fixed_size_chunk(document: Document, chunk_size: int = 1000, overlap: int = 100) -> List[DocumentChunk]:
    """Simple fixed-size character chunking (fallback)."""
    chunks = []
    content = document.content
    
    for i in range(0, len(content), chunk_size - overlap):
        chunk_content = content[i:i + chunk_size]
        if len(chunk_content.strip()) < 50:
            continue
        
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=len(chunks),
            content=chunk_content.strip(),
            metadata={
                "document_name": document.name,
                "section": "full_document",
                "source": document.source.value if hasattr(document.source, 'value') else str(document.source),
                "version": document.version,
                "chunk_type": "fixed_size",
                "start_char": i,
                "end_char": min(i + chunk_size, len(content))
            }
        )
        chunks.append(chunk)
    
    return chunks