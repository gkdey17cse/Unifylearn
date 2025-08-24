# src/app/services/plan_builder.py
from typing import Dict, List, Any
from src.app.utils.config import (
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

# Canonical provider keys (lowercase) → DB + Collection + fields to search
PROVIDERS: Dict[str, Dict[str, Any]] = {
    "coursera": {
        "db": MONGO_DB_COURSERA,
        "coll": COLL_COURSERA,
        "text_fields": [
            "Title",
            "Short Intro",
            "Skills",
            "Category",
            "Sub-Category",
            "Rating",
            "Number of viewers",
            "URL",
        ],
    },
    "futurelearn": {
        "db": MONGO_DB_FUTURELEARN,
        "coll": COLL_FUTURELEARN,
        "text_fields": [
            # both wide & course-level fields appear in your CSV
            "Title",
            "Short Intro",
            "Category",
            "Course Title",
            "Course Short Intro",
            "Topics related to CRM",
            "URL",
            "Duration",
        ],
    },
    "simplilearn": {
        "db": MONGO_DB_SIMPLILEARN,
        "coll": COLL_SIMPLILEARN,
        "text_fields": ["Title", "Short Intro", "Category", "Sub-Category", "Skills","URL","Rating"],
    },
    "udacity": {
        "db": MONGO_DB_UDACITY,
        "coll": COLL_UDACITY,
        "text_fields": [
            "Title",
            "Short Intro",
            "Category",
            "What you learn",
            "Prequisites",
            "Sub-Category",
            "URL",
            "Duration",
        ],
    },
}

# Accept lots of synonyms / spellings for platform names
PROVIDER_ALIASES = {
    "coursera": "coursera",
    "courseradb": "coursera",
    "futurelearn": "futurelearn",
    "future learn": "futurelearn",
    "simplilearn": "simplilearn",
    "simpli learn": "simplilearn",
    "udacity": "udacity",
}

LEVEL_SYNONYMS = {
    "beginner": [
        "beginner",
        "beginners",
        "intro",
        "introductory",
        "foundation",
        "foundations",
        "basic",
    ],
    "intermediate": ["intermediate"],
    "advanced": ["advanced", "expert"],
}


def _canon_platforms(platforms):
    if not platforms:
        return list(PROVIDERS.keys())
    keys = []
    for p in platforms:
        k = PROVIDER_ALIASES.get(str(p).strip().lower())
        if k and k not in keys:
            keys.append(k)
    return keys or list(PROVIDERS.keys())


def _level_regex(level: str) -> Dict[str, Any]:
    if not level:
        return {}
    lvl = str(level).lower().strip()
    alts = []
    for base, syns in LEVEL_SYNONYMS.items():
        if lvl in syns or lvl == base:
            alts = syns
            break
    pattern = "|".join(sorted(set([lvl] + alts), key=len, reverse=True))
    # match common level fields if present
    return {
        "$or": [
            {"Level": {"$regex": pattern, "$options": "i"}},
            {"Difficulty": {"$regex": pattern, "$options": "i"}},
            {
                "Course Type": {"$regex": pattern, "$options": "i"}
            },  # sometimes stores Beginner etc.
        ]
    }


def _topic_regex(topic: str, fields: List[str]) -> Dict[str, Any]:
    if not topic:
        return {}
    return {"$or": [{f: {"$regex": topic, "$options": "i"}} for f in fields]}


def build_plans(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build Mongo query plans using *real* DB/collection/field shapes.
    parsed expects keys: topic:str, level:str|None, platforms:list|None, limit:int|None
    """
    topic = (parsed or {}).get("topic")
    level = (parsed or {}).get("level")
    limit = (parsed or {}).get("limit") or DEFAULT_PER_PROVIDER_LIMIT

    if not isinstance(limit, int) or limit <= 0:
        limit = DEFAULT_PER_PROVIDER_LIMIT
    limit = min(limit, MAX_PER_PROVIDER_LIMIT)

    provider_keys = _canon_platforms((parsed or {}).get("platforms"))
    plans: List[Dict[str, Any]] = []

    for key in provider_keys:
        meta = PROVIDERS.get(key)
        if not meta:
            continue

        # Build $and of topic + level (when present)
        clauses = []
        tr = _topic_regex(topic, meta["text_fields"])
        if tr:
            clauses.append(tr)
        lr = _level_regex(level)
        if lr:
            clauses.append(lr)

        mongo_filter = {"$and": clauses} if clauses else {}

        # One wide projection that covers all columns you showed
        projection = {
            "_id": 0,
            # common
            "Title": 1,
            "URL": 1,
            "Short Intro": 1,
            "Category": 1,
            "Sub-Category": 1,
            "Course Type": 1,
            "Language": 1,
            "Subtitle Languages": 1,
            "Skills": 1,
            "Instructors": 1,
            "Rating": 1,
            "Number of viewers": 1,
            "Duration": 1,
            "Site": 1,
            # futurelearn-specific (plus duplicates for convenience)
            "Program Type": 1,
            "Courses": 1,
            "Level": 1,
            "Topics related to CRM": 1,
            "ExpertTracks": 1,
            "FAQs": 1,
            "Course Title": 1,
            "Course URL": 1,
            "Course Short Intro": 1,
            "Weekly study": 1,
            "Premium course": 1,
            # udacity-specific
            "Prequisites": 1,
            "Prerequisites": 1,
            "What you learn": 1,
        }

        plans.append(
            {
                "provider": key,
                "db": meta["db"],
                "coll": meta["coll"],
                "filter": mongo_filter,
                "projection": projection,
                "limit": limit,
            }
        )

    return plans
