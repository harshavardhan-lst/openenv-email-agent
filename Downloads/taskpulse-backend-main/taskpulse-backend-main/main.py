"""
ASGI entry shim — run the API from the **repository root** (folder that contains `backend/`).

    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

Do not `cd backend` first; imports expect the parent directory on sys.path.
"""

from backend.app import app

__all__ = ["app"]
