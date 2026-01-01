# src/app/query_executor/provider_executor.py
import re
import json
from src.app.db_connection import dbMap, COLLECTION_MAP
from src.app.query_generator.query_translator import translate_query_to_db_fields
from bson import ObjectId, Decimal128
import math

STOPWORDS = {
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
    "show",
    "me",
    "all",
    "from",
    "any",
    "platform",
    "only",
    "related",
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


def build_keyword_fallback_query(user_query, provider):
    """
    Builds intelligent fallback queries that preserve semantic context.
    """
    # Extract meaningful phrases with context preservation
    phrases = _extract_meaningful_phrases(user_query)

    if not phrases:
        return {}

    # Use actual database field names for each provider
    search_fields = {
        "coursera": ["Title", "Short Intro", "Skills", "Category", "Sub-Category"],
        "udacity": ["Title", "Short Intro", "What you learn", "Level"],
        "simplilearn": ["Title", "Short Intro", "Skills", "Category"],
        "futurelearn": ["Title", "Short Intro", "Category", "Duration"],
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
        # Use OR to broaden search
        return {"$or": fallback_conditions}
    else:
        return {}


def _extract_find_query_from_schema(schema_field_query):
    """
    Extract the actual find query from schema query structure.
    """
    if not schema_field_query:
        return {}

    # If it's already a proper find query (has MongoDB operators)
    if any(key.startswith("$") for key in schema_field_query.keys()):
        return schema_field_query

    # If it's empty query for a provider that shouldn't be queried
    if schema_field_query == {}:
        return {}

    # If it's wrapped in a "query" key but contains direct conditions
    if "query" in schema_field_query:
        query_content = schema_field_query["query"]
        # If it contains actual conditions (not aggregation stages)
        if query_content and not any(
            key.startswith("$") for key in query_content.keys()
        ):
            return query_content
        # If it has $match, extract from $match
        elif isinstance(query_content, dict) and "$match" in query_content:
            return query_content["$match"]
        else:
            return query_content

    # Default: return as is
    return schema_field_query


def _is_valid_find_query(query):
    """
    Validate that the query is a proper MongoDB find query
    """
    if not query:
        return False

    if not isinstance(query, dict):
        return False

    # Empty query means fetch all - we want to avoid this for SPJ queries
    if query == {}:
        return False

    # Check if it has proper MongoDB operators or field conditions
    has_conditions = any(
        key.startswith("$")  # MongoDB operators
        or isinstance(value, dict)
        and any(subkey.startswith("$") for subkey in value.keys())  # Field operators
        for key, value in query.items()
    )

    return has_conditions


def _extract_limit_from_query(query_obj):
    """
    Extract $limit from query and remove it from the main query
    Returns: (clean_query, limit_value)
    """
    limit_value = None

    if isinstance(query_obj, dict):
        # Check for $limit at top level
        if "$limit" in query_obj:
            limit_value = query_obj["$limit"]
            clean_query = {k: v for k, v in query_obj.items() if k != "$limit"}
            return clean_query, limit_value

        # Check for $limit in $and conditions
        if "$and" in query_obj and isinstance(query_obj["$and"], list):
            new_and_conditions = []
            for condition in query_obj["$and"]:
                if isinstance(condition, dict) and "$limit" in condition:
                    limit_value = condition["$limit"]
                else:
                    new_and_conditions.append(condition)

            if new_and_conditions:
                clean_query = {"$and": new_and_conditions}
            else:
                clean_query = {}
            return clean_query, limit_value

    return query_obj, limit_value


def execute_provider_query(provider, schema_field_query, user_query):
    """
    Execute query for a specific provider with fallback mechanism
    """
    provider_lower = provider.lower()
    db = dbMap.get(provider_lower)

    if db is None:
        print(f"❌ Database not configured for provider: {provider_lower}")
        return None, {"error": "DB not configured"}

    collection_name = COLLECTION_MAP.get(provider_lower)
    coll = db.get_collection(collection_name)

    print(f"🔧 Processing schema query for {provider_lower}")
    print(f"📋 Original Schema Query: {json.dumps(schema_field_query, indent=2)}")

    # STEP 1: Extract the actual find query from schema structure
    find_query = _extract_find_query_from_schema(schema_field_query)
    print(f"🔍 Extracted Find Query: {json.dumps(find_query, indent=2)}")

    # VALIDATION: Skip if this is an empty query for SPJ
    if not _is_valid_find_query(find_query):
        print(f"⏭️  Skipping {provider} - no valid query conditions")
        return [], {
            "collection": collection_name,
            "query": {},
            "match_count": 0,
            "used_fallback": False,
            "limit_applied": None,
            "execution_error": "No valid query conditions - provider skipped",
            "skipped": True,
        }

    # STEP 2: Extract limit before translation
    clean_find_query, limit_value = _extract_limit_from_query(find_query)
    print(f"📏 Extracted limit: {limit_value}")

    # STEP 3: Translate query from schema fields to database fields
    db_field_query = translate_query_to_db_fields(clean_find_query, provider_lower)

    print(f"🔄 Translated Database Query: {json.dumps(db_field_query, indent=2)}")

    final_query_used = db_field_query
    used_fallback = False
    execution_error = None

    try:
        # Execute the translated query with limit
        print(f"🚀 Executing find query on {provider_lower}.{collection_name}")

        if limit_value:
            cursor = coll.find(db_field_query).limit(limit_value)
            print(f"📏 Applying limit: {limit_value}")
        else:
            cursor = coll.find(db_field_query)

        matched_docs = list(cursor)

        print(f"📄 Found {len(matched_docs)} documents with primary query")

        # Fallback if no results
        if len(matched_docs) == 0:
            print("🔄 No results with primary query, trying fallback...")
            used_fallback = True
            fallback_query = build_keyword_fallback_query(user_query, provider_lower)
            final_query_used = fallback_query
            print(f"🔄 Fallback Query: {json.dumps(fallback_query, indent=2)}")

            if limit_value:
                cursor = coll.find(fallback_query).limit(limit_value)
            else:
                cursor = coll.find(fallback_query)

            matched_docs = list(cursor)
            print(f"📄 Found {len(matched_docs)} documents with fallback query")

        # Sanitize documents
        sanitized_docs = [sanitize_doc(doc) for doc in matched_docs]

        result_info = {
            "collection": collection_name,
            "query": final_query_used,
            "match_count": len(sanitized_docs),
            "used_fallback": used_fallback,
            "limit_applied": limit_value,
            "execution_error": execution_error,
        }

        return sanitized_docs, result_info

    except Exception as e:
        error_msg = f"Failed to execute query for {provider}: {str(e)}"
        print(f"❌ Query execution error: {error_msg}")
        return None, {
            "collection": collection_name,
            "query": final_query_used,
            "match_count": 0,
            "used_fallback": used_fallback,
            "limit_applied": limit_value,
            "execution_error": error_msg,
        }
