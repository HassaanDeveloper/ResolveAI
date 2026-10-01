#!/usr/bin/env python
"""
ResolveAI Document Ingestion Script
Part 08: Knowledge Documents & RAG Ingestion

Run this script to ingest all policy documents into Supabase with Gemini embeddings.

Usage:
    python ingest_documents.py
    python ingest_documents.py --reset  # Delete existing and re-ingest
    python ingest_documents.py --file data/documents/refund_policy_v2.1.md  # Ingest single file
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.rag import (
    ingestion_service,
    Document,
    DocumentSource,
    DocumentStatus,
)
from app.services.database import get_supabase_client, reset_supabase_client

setup_logging("INFO")
logger = get_logger(__name__)

# Document configuration: (filename, document_name, source, version)
DOCUMENTS_TO_INGEST: List[Tuple[str, str, str, str]] = [
    ("refund_policy_v2.1.md", "Northstar Commerce Refund Policy", "internal-policy", "2.1"),
    ("cancellation_policy_v1.3.md", "Northstar Commerce Order Cancellation Policy", "internal-policy", "1.3"),
    ("shipping_policy_v1.5.md", "Northstar Commerce Shipping Policy", "internal-policy", "1.5"),
    ("escalation_sop_v1.0.md", "Northstar Commerce Escalation SOP", "internal-sop", "1.0"),
    ("customer_service_sop_v2.0.md", "Northstar Commerce Customer Service SOP", "internal-sop", "2.0"),
    ("refund_approval_matrix_v1.0.md", "Northstar Commerce Refund Approval Matrix", "internal-policy", "1.0"),
    ("exception_handling_policy_v1.2.md", "Northstar Commerce Exception Handling Policy", "internal-policy", "1.2"),
]


async def check_prerequisites() -> bool:
    """Check that all prerequisites are met."""
    # Check Gemini API key
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
        logger.error("GEMINI_API_KEY not configured in .env")
        return False
    
    # Check Supabase credentials
    if not settings.SUPABASE_URL or settings.SUPABASE_URL == "https://your-project.supabase.co":
        logger.error("SUPABASE_URL not configured in .env")
        return False
    
    if not settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_SERVICE_KEY == "your-supabase-service-key-here":
        logger.error("SUPABASE_SERVICE_KEY not configured in .env")
        return False
    
    # Check document files exist
    docs_dir = Path(__file__).parent.parent / "data" / "documents"
    missing = []
    for filename, _, _, _ in DOCUMENTS_TO_INGEST:
        if not (docs_dir / filename).exists():
            missing.append(filename)
    
    if missing:
        logger.error(f"Missing document files: {missing}")
        return False
    
    logger.info("All prerequisites met")
    return True


async def reset_database() -> bool:
    """Delete all existing documents and chunks."""
    logger.info("Resetting database (deleting existing documents and chunks)...")
    
    try:
        client = get_supabase_client()
        
        # Delete all chunks first
        client.table("document_chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        # Delete all documents
        client.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        logger.info("Database reset complete")
        return True
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False


async def ingest_single_file(file_path: str, document_name: str, source: str, version: str) -> bool:
    """Ingest a single document file."""
    logger.info(f"Ingesting: {document_name} from {file_path}")
    
    result = await ingestion_service.ingest_from_file(
        file_path=file_path,
        document_name=document_name,
        source=source,
        version=version
    )
    
    if result.success:
        logger.info(f"✓ Success: {document_name} - {result.chunks_created} chunks, {result.embeddings_stored} embeddings ({result.processing_time_ms}ms)")
        return True
    else:
        logger.error(f"✗ Failed: {document_name} - {result.error}")
        return False


async def ingest_all_documents(reset: bool = False) -> dict:
    """Ingest all configured documents."""
    if reset:
        if not await reset_database():
            return {"success": False, "error": "Failed to reset database"}
    
    docs_dir = Path(__file__).parent.parent / "data" / "documents"
    results = {"success": 0, "failed": 0, "details": []}
    
    for filename, doc_name, source, version in DOCUMENTS_TO_INGEST:
        file_path = str(docs_dir / filename)
        success = await ingest_single_file(file_path, doc_name, source, version)
        
        results["details"].append({
            "document": doc_name,
            "file": filename,
            "success": success
        })
        
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
    
    return results


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ResolveAI Document Ingestion")
    parser.add_argument("--reset", action="store_true", help="Delete existing documents before ingesting")
    parser.add_argument("--file", type=str, help="Ingest a single file (provide filename only)")
    parser.add_argument("--name", type=str, help="Document name (required with --file)")
    parser.add_argument("--source", type=str, default="internal-policy", help="Document source (required with --file)")
    parser.add_argument("--version", type=str, default="1.0", help="Document version (required with --file)")
    
    args = parser.parse_args()
    
    # Check prerequisites
    if not await check_prerequisites():
        sys.exit(1)
    
    try:
        if args.file:
            # Single file ingestion
            file_path = str(Path(__file__).parent.parent / "data" / "documents" / args.file)
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                sys.exit(1)
            
            if not args.name:
                logger.error("--name required when using --file")
                sys.exit(1)
            
            success = await ingest_single_file(file_path, args.name, args.source, args.version)
            sys.exit(0 if success else 1)
        else:
            # Ingest all documents
            results = await ingest_all_documents(reset=args.reset)
            
            print("\n" + "="*60)
            print("INGESTION SUMMARY")
            print("="*60)
            print(f"Successful: {results['success']}")
            print(f"Failed: {results['failed']}")
            
            for detail in results["details"]:
                status = "✓" if detail["success"] else "✗"
                print(f"  {status} {detail['document']} ({detail['file']})")
            
            if results["failed"] > 0:
                sys.exit(1)
            else:
                print("\nAll documents ingested successfully!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        reset_supabase_client()


if __name__ == "__main__":
    asyncio.run(main())