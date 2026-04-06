"""MongoDB client and database handle for TaskPulse."""

import logging
import os
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_mongodb_uri() -> str:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return uri


def get_database_name() -> str:
    return os.getenv("MONGODB_DB_NAME", "taskpulse")


def get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = get_mongodb_uri()
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        logger.info("Connected to MongoDB at %s", uri.split("@")[-1] if "@" in uri else uri)
    return _client


def get_database() -> Database:
    return get_client()[get_database_name()]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed")
