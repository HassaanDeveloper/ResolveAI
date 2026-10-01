"""Vercel Python entrypoint for the ResolveAI backend.

The ASGI application lives at app.main:app. This module re-exports it under the
conventional `api/index.py` path that Vercel's Python runtime looks for when the
service root is `backend`. It exists only as a deployment adapter and contains
no application logic.
"""

from app.main import app

__all__ = ["app"]