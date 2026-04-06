"""User registration and account deletion."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from backend.database.mongodb_connection import get_database
from backend.database import repository as repo
from backend.schemas import UserCreate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db() -> Database:
    return get_database()


@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Database = Depends(get_db)):
    doc = repo.create_user(db, user.name)
    logger.info("Created user %s", doc["_id"])
    return UserResponse(id=str(doc["_id"]), name=doc["name"], total_rewards=doc.get("total_rewards", 0))


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Database = Depends(get_db)):
    ok = repo.delete_user_cascade(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Deleted user %s", user_id)
    return {"message": "User and related data deleted successfully"}
