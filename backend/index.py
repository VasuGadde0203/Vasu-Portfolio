"""Vercel entry point: Vercel looks for a module-level ASGI `app` in index.py.

Locally and on Railway/Docker, use `uvicorn app.main:app_factory --factory` instead.
"""

from app.main import create_app

app = create_app()
