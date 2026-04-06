"""Reward history endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pymongo.database import Database

from backend.database.mongodb_connection import get_database
from backend.database import repository as repo

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db() -> Database:
    return get_database()


@router.get("/rewards/{user_id}")
def get_rewards(user_id: str, db: Database = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = repo.list_rewards_for_user(db, user_id)
    out = []
    for r in rows:
        out.append(
            {
                "id": str(r["_id"]),
                "user_id": str(r["user_id"]),
                "reward_name": r.get("reward_name"),
                "earned_at": r.get("earned_at"),
            }
        )
    return out
