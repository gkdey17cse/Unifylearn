# src/app/services/db_service.py
# central abstraction for connecting to Mongo. We use find (not aggregation) to keep it simple and read-only.
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from typing import List, Dict, Any, Optional
from src.app.utils.config import MONGO_URI

_client = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not MONGO_URI:
            raise RuntimeError("MONGO_URI not set in environment / config")
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # ping to raise early error if needed
        try:
            _client.admin.command("ping")
        except ServerSelectionTimeoutError as e:
            # let app continue but raise to caller if they want hard failure
            raise RuntimeError(f"Could not connect to MongoDB: {e}")
    return _client

def find_documents(db_name: str, coll_name: str, filter_doc: Dict[str, Any], projection: Optional[Dict[str, int]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    client = get_client()
    coll = client[db_name][coll_name]
    cursor = coll.find(filter_doc, projection or {}).limit(limit)
    return list(cursor)
