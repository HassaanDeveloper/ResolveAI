#!/usr/bin/env python
"""
ResolveAI Seed Runner
Part 04: Synthetic Northstar Commerce Data

Run this script to seed the Supabase database with synthetic data.
Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file.

Usage:
    python run_seeds.py
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


def run_seeds():
    """Run all seed SQL files in order."""
    try:
        from supabase import create_client
    except ImportError:
        logger.error("supabase-py not installed. Run: pip install supabase")
        return False

    # Check credentials
    if not settings.SUPABASE_URL or settings.SUPABASE_URL == "https://your-project.supabase.co":
        logger.error("SUPABASE_URL not configured in .env")
        return False

    if not settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_SERVICE_KEY == "your-supabase-service-key-here":
        logger.error("SUPABASE_SERVICE_KEY not configured in .env")
        return False

    logger.info("Connecting to Supabase...")
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    seed_files = [
        "seed_all.sql",
    ]

    seeds_dir = Path(__file__).parent

    for seed_file in seed_files:
        file_path = seeds_dir / seed_file
        if not file_path.exists():
            logger.error(f"Seed file not found: {file_path}")
            return False

        logger.info(f"Running seed: {seed_file}")
        sql = file_path.read_text()

        # Split by semicolon and execute each statement
        # Note: This is a simple splitter; for production use a proper SQL parser
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, stmt in enumerate(statements):
            if not stmt:
                continue
            try:
                # Execute raw SQL via rpc or direct query
                # Supabase Python client doesn't have direct SQL execution
                # We'll use the REST API
                import httpx
                response = httpx.post(
                    f"{settings.SUPABASE_URL}/rest/v1/rpc/exec_sql",
                    headers={
                        "apikey": settings.SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"sql": stmt},
                    timeout=30.0,
                )
                if response.status_code >= 400:
                    logger.warning(f"Statement {i+1} failed: {response.text[:200]}")
                else:
                    logger.debug(f"Statement {i+1} executed")
            except Exception as e:
                logger.warning(f"Statement {i+1} error: {e}")

        logger.info(f"Completed: {seed_file}")

    logger.info("All seeds completed!")
    return True


if __name__ == "__main__":
    success = run_seeds()
    sys.exit(0 if success else 1)