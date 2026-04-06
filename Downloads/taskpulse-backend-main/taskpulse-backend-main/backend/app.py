"""TaskPulse API — FastAPI application entrypoint."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.database.mongodb_connection import close_client, get_database
from backend.database.repository import ensure_indexes
from backend.routes import auth_routes, reward_routes, task_routes
from backend.services import fraud_detection_service
from backend.utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    try:
        db = get_database()
        ensure_indexes(db)
    except Exception:
        # Logged by Mongo client; allow app to start for health/debug
        import logging

        logging.getLogger(__name__).exception("MongoDB startup connection failed")
    fraud_detection_service.load_fraud_model()
    yield
    close_client()


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="TaskPulse Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(task_routes.router)
app.include_router(reward_routes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
