"""Shared helpers for IDs, dates, and submission metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId


def parse_object_id(value: str) -> Optional[ObjectId]:
    if not value or not isinstance(value, str):
        return None
    try:
        return ObjectId(value.strip())
    except InvalidId:
        return None


def user_account_age_days(created_at: Optional[datetime]) -> int:
    if created_at is None:
        return 0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - created_at
    return max(0, int(delta.total_seconds() // 86400))


def start_of_local_day_utc(hour_offset: int = 0) -> datetime:
    """UTC midnight adjusted by offset; used for 'tasks completed today' proxy."""
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)
