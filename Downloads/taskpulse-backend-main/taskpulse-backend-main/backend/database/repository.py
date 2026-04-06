"""MongoDB CRUD helpers for users, tasks, quizzes, and rewards."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

from backend.utils.helper_functions import parse_object_id

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_user(db: Database, name: str) -> Dict[str, Any]:
    doc = {
        "name": name.strip(),
        "total_rewards": 0,
        "created_at": _utcnow(),
    }
    res = db["users"].insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def get_user_by_id(db: Database, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None
    return db["users"].find_one({"_id": oid})


def delete_user_cascade(db: Database, user_id: str) -> bool:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return False

    tasks = list(db["tasks"].find({"user_id": oid}, {"_id": 1}))
    task_ids = [t["_id"] for t in tasks]

    if task_ids:
        db["quizzes"].delete_many({"task_id": {"$in": task_ids}})
        db["tasks"].delete_many({"_id": {"$in": task_ids}})

    db["reward_history"].delete_many({"user_id": oid})
    result = db["users"].delete_one({"_id": oid})
    return result.deleted_count > 0


def create_task(db: Database, user_id: str, summary: str) -> Dict[str, Any]:
    uid = parse_object_id(user_id)
    if uid is None:
        raise ValueError("Invalid user id")
    doc = {
        "user_id": uid,
        "summary": summary.strip(),
        "status": "pending",
        "created_at": _utcnow(),
    }
    res = db["tasks"].insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def get_task_by_id(db: Database, task_id: str) -> Optional[Dict[str, Any]]:
    try:
        tid = ObjectId(task_id)
    except InvalidId:
        return None
    return db["tasks"].find_one({"_id": tid})


def list_tasks_for_user(db: Database, user_id: str) -> List[Dict[str, Any]]:
    uid = parse_object_id(user_id)
    if uid is None:
        return []
    return list(db["tasks"].find({"user_id": uid}).sort("created_at", -1))


def update_task_status(db: Database, task_id: str, status: str) -> None:
    tid = parse_object_id(task_id)
    if tid is None:
        raise ValueError("Invalid task id")
    db["tasks"].update_one({"_id": tid}, {"$set": {"status": status}})


def set_task_quiz_questions(
    db: Database, task_id: str, questions: List[Dict[str, Any]]
) -> None:
    tid = parse_object_id(task_id)
    if tid is None:
        raise ValueError("Invalid task id")
    db["tasks"].update_one(
        {"_id": tid},
        {"$set": {"quiz_questions": questions, "quiz_generated_at": _utcnow()}},
    )


def increment_user_rewards(db: Database, user_id: str, delta: int = 1) -> None:
    uid = parse_object_id(user_id)
    if uid is None:
        raise ValueError("Invalid user id")
    db["users"].update_one({"_id": uid}, {"$inc": {"total_rewards": delta}})


def insert_reward_history(db: Database, user_id: str, reward_name: str) -> None:
    uid = parse_object_id(user_id)
    if uid is None:
        raise ValueError("Invalid user id")
    db["reward_history"].insert_one(
        {
            "user_id": uid,
            "reward_name": reward_name,
            "earned_at": _utcnow(),
        }
    )


def list_rewards_for_user(db: Database, user_id: str) -> List[Dict[str, Any]]:
    uid = parse_object_id(user_id)
    if uid is None:
        return []
    return list(db["reward_history"].find({"user_id": uid}).sort("earned_at", -1))


def get_quiz_for_task(db: Database, task_id: str) -> Optional[Dict[str, Any]]:
    tid = parse_object_id(task_id)
    if tid is None:
        return None
    return db["quizzes"].find_one({"task_id": tid})


def insert_quiz(
    db: Database,
    task_id: str,
    score: int,
    fraud_probability: float,
    reward_granted: bool,
    explanation: str,
    task_similarity: float,
) -> None:
    tid = parse_object_id(task_id)
    if tid is None:
        raise ValueError("Invalid task id")
    db["quizzes"].insert_one(
        {
            "task_id": tid,
            "score": score,
            "fraud_probability": fraud_probability,
            "reward_granted": reward_granted,
            "explanation": explanation,
            "task_similarity": task_similarity,
            "created_at": _utcnow(),
        }
    )


def count_user_tasks_since(db: Database, user_id: str, since: datetime) -> int:
    uid = parse_object_id(user_id)
    if uid is None:
        return 0
    return db["tasks"].count_documents({"user_id": uid, "created_at": {"$gte": since}})


def average_quiz_score_for_user(db: Database, user_id: str) -> float:
    uid = parse_object_id(user_id)
    if uid is None:
        return 0.0
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$lookup": {"from": "quizzes", "localField": "_id", "foreignField": "task_id", "as": "q"}},
        {"$unwind": "$q"},
        {"$group": {"_id": None, "avg_score": {"$avg": "$q.score"}}},
    ]
    rows = list(db["tasks"].aggregate(pipeline))
    if not rows or rows[0].get("avg_score") is None:
        return 0.0
    return float(rows[0]["avg_score"])


def ensure_indexes(db: Database) -> None:
    try:
        db["tasks"].create_index([("user_id", 1), ("created_at", -1)])
        db["quizzes"].create_index("task_id", unique=True)
        db["reward_history"].create_index([("user_id", 1), ("earned_at", -1)])
    except Exception as e:
        logger.warning("Index creation skipped or failed: %s", e)
