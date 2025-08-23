# src/app/services/plan_builder.py
from typing import Dict, List, Any
from app.utils.config import (
    MONGO_DB_COURSERA,
    MONGO_DB_FUTURELEARN,
    MONGO_DB_SIMPLILEARN,
    MONGO_DB_UDACITY,
    COLL_COURSERA,
    COLL_FUTURELEARN,
    COLL_SIMPLILEARN,
    COLL_UDACITY,
    DEFAULT_PER_PROVIDER_LIMIT,
    MAX_PER_PROVIDER_LIMIT,
)

# field lists per provider - these are the columns in your collections
FIELDS_PER_PROVIDER = {
    "coursera": {
        "db": MONGO_DB_COURSERA,
        "coll": COLL_COURSERA,
        "text_fields": [
            "Title",
            "Skills",
            "Short Intro",
            "Category",
            "Sub-Category",
            "Site",
        ],
    },
    "futurelearn": {
        "db": MONGO_DB_FUTURELEARN,
        "coll": COLL_FUTURELEARN,
        # Note the space in "Course Title" and "Course Short Intro"
        "text_fields": [
            "Course Title",
            "Course Short Intro",
            "Title",
            "Topics related to CRM",
            "Category",
        ],
    },
    "simplilearn": {
        "db": MONGO_DB_SIMPLILEARN,
        "coll": COLL_SIMPLILEARN,
        "text_fields": ["Title", "Skills", "Short Intro", "Category"],
    },
    "udacity": {
        "db": MONGO_DB_UDACITY,
        "coll": COLL_UDACITY,
        "text_fields": ["Title", "What you learn", "Short Intro", "Category"],
    },
}


def _regex_or_for_topic(topic: str, fields: List[str]):
    """
    Build a Mongo $or filter with case-insensitive regex on the specified fields.
    """
    if not topic:
        return {}
    predicate = {"$or": [{f: {"$regex": topic, "$options": "i"}} for f in fields]}
    return predicate


def build_plans(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns list of plans:
      { provider_key, db, coll, filter, projection, limit }
    """
    topic = parsed.get("topic")
    platforms = parsed.get("platforms")  # None => all
    limit = parsed.get("limit") or DEFAULT_PER_PROVIDER_LIMIT
    # sanitize limit
    if not isinstance(limit, int) or limit <= 0:
        limit = DEFAULT_PER_PROVIDER_LIMIT
    limit = min(limit, MAX_PER_PROVIDER_LIMIT)

    provider_keys = list(FIELDS_PER_PROVIDER.keys()) if not platforms else platforms

    plans = []
    for key in provider_keys:
        meta = FIELDS_PER_PROVIDER.get(key)
        if not meta:
            continue
        filt = _regex_or_for_topic(topic, meta["text_fields"]) if topic else {}
        # small projection to include important fields (we will normalize client-side)
        projection = {
            "_id": 0,
            "Title": 1,
            "URL": 1,
            "Course URL": 1,
            "CourseTitle": 1,
            "Short Intro": 1,
            "Course Short Intro": 1,
            "Skills": 1,
            "What you learn": 1,
            "Rating": 1,
            "Number of viewers": 1,
            "Duration": 1,
            "Site": 1,
        }
        plans.append(
            {
                "provider": key,
                "db": meta["db"],
                "coll": meta["coll"],
                "filter": filt,
                "projection": projection,
                "limit": limit,
            }
        )
    return plans
