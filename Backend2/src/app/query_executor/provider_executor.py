import re
from src.app.db_connection import dbMap, COLLECTION_MAP
from src.app.query_generator.query_translator import translate_query_to_db_fields
from bson import ObjectId, Decimal128
import math

STOPWORDS = {
    # ... (keep existing STOPWORDS) ...
    "course",
    "courses",
    "program",
    "programs",
    "class",
    "classes",
    "training",
    "learn",
    "learning",
    "study",
    "studying",
    "online",
    "free",
    "paid",
    "certificate",
    "certification",
    "degree",
    "diploma",
}


def sanitize_value(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, Decimal128):
        try:
            return float(v.to_decimal())
        except Exception:
            return str(v)
    if isinstance(v, dict):
        return {k: sanitize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [sanitize_value(i) for i in v]
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    return v


def sanitize_doc(doc):
    return sanitize_value(doc)


def build_keyword_fallback_query(user_query, provider):
    """
    Builds intelligent fallback queries that preserve semantic context.
    """
    # Extract meaningful phrases with context preservation
    phrases = _extract_meaningful_phrases(user_query)

    if not phrases:
        return {}

    search_fields = {
        "coursera": ["Title", "Short Intro", "Skills", "Category", "Sub-Category"],
        "udacity": ["Title", "Short Intro", "What you learn", "Category"],
        "simplilearn": ["Title", "Short Intro", "Skills", "Category"],
        "futurelearn": ["Title", "Short Intro", "Category", "Sub-Category"],
    }
    fields_to_search = search_fields.get(provider, ["Title", "Short Intro"])

    # Build query with preserved context
    fallback_conditions = []
    for phrase in phrases:
        for field in fields_to_search:
            # Use word boundaries for exact matching
            condition = {
                field: {"$regex": f"\\b{re.escape(phrase)}\\b", "$options": "i"}
            }
            fallback_conditions.append(condition)

    if fallback_conditions:
        # Use AND to ensure all important context is preserved
        return {"$and": [{"$or": fallback_conditions}]}
    else:
        return {}


def _extract_meaningful_phrases(user_query):
    """
    Extract semantically meaningful phrases from the query.
    """
    # Preserve quoted phrases
    quoted_phrases = re.findall(r"\"([^\"]+)\"", user_query)

    # Preserve technical terms and compound phrases
    technical_phrases = re.findall(r"[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*", user_query)

    # Combine and filter
    all_phrases = quoted_phrases + technical_phrases
    meaningful_phrases = []

    for phrase in all_phrases:
        phrase_lower = phrase.lower()
        # Filter out stopwords and very short phrases
        words = phrase_lower.split()
        meaningful_words = [
            word for word in words if word not in STOPWORDS and len(word) > 2
        ]

        if meaningful_words:
            meaningful_phrase = " ".join(meaningful_words)
            if len(meaningful_phrase) > 3:  # Minimum meaningful phrase length
                meaningful_phrases.append(meaningful_phrase)

    return list(set(meaningful_phrases))  # Remove duplicates


def execute_provider_query(provider, schema_field_query, user_query):
    """
    Execute query for a specific provider with fallback mechanism
    """
    provider_lower = provider.lower()
    db = dbMap.get(provider_lower)

    if db is None:
        return None, {"error": "DB not configured"}

    collection_name = COLLECTION_MAP.get(provider_lower)
    coll = db.get_collection(collection_name)

    # Translate query
    db_field_query = translate_query_to_db_fields(schema_field_query, provider_lower)

    final_query_used = db_field_query
    used_fallback = False
    execution_error = None

    try:
        # Execute the translated query
        cursor = coll.find(db_field_query)
        matched_docs = list(cursor)

        # Fallback if no results
        if len(matched_docs) == 0:
            used_fallback = True
            fallback_query = build_keyword_fallback_query(user_query, provider_lower)
            final_query_used = fallback_query
            cursor = coll.find(fallback_query)
            matched_docs = list(cursor)

        # Sanitize documents
        sanitized_docs = [sanitize_doc(doc) for doc in matched_docs]

        result_info = {
            "collection": collection_name,
            "query": final_query_used,
            "match_count": len(sanitized_docs),
            "used_fallback": used_fallback,
            "execution_error": execution_error,
        }

        return sanitized_docs, result_info

    except Exception as e:
        error_msg = f"Failed to execute query for {provider}: {str(e)}"
        return None, {
            "collection": collection_name,
            "query": final_query_used,
            "match_count": 0,
            "used_fallback": used_fallback,
            "execution_error": error_msg,
        }
