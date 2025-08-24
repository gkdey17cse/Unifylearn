# src/app/query_handler.py
import os
import re
import json
import math
from datetime import datetime
from src.app.db_connection import dbMap, COLLECTION_MAP
from src.app.response_formatter import unifyResponse
from src.app.schema_loader import getSchemasAndSamples
import google.generativeai as genai
from bson import ObjectId, Decimal128

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Output directory from environment variable
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./results")

# --- CRITICAL: Mapping from Schema Field Names to Database Field Names ---
SCHEMA_TO_DB_FIELD_MAP = {
    "coursera": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Skills Covered": "Skills",
        "Main Category": "Category",
        "Sub-Category": "Sub-Category",
        "Average Rating": "Rating",
        "Estimated Duration": "Duration",
    },
    "futurelearn": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Main Category": "Category",
        "Estimated Duration": "Duration",
    },
    "simplilearn": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Main Category": "Category",
        "Skills Covered": "Skills",
    },
    "udacity": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Estimated Duration": "Duration",
        "Program Type": "Program Type",
    },
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


def _find_balanced_json(text: str):
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    starts = [i for i, c in enumerate(text) if c == "{"]
    candidates = []
    for i in starts:
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[i : j + 1])
                    break
    candidates.sort(key=len, reverse=True)
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            continue
    return None


def build_keyword_fallback_query(user_query, provider):
    """
    Builds a more flexible, keyword-based query as a fallback.
    Splits the user's query into important words and searches for them in the most common fields.
    """
    stopwords = {
        "give",
        "me",
        "a",
        "the",
        "and",
        "or",
        "from",
        "for",
        "course",
        "courses",
        "on",
        "in",
        "about",
        "named",
        "something",
        "related",
        "to",
        "with",
    }
    keywords = [
        word
        for word in re.split(r"\W+", user_query)
        if word.lower() not in stopwords and len(word) > 2
    ]

    if not keywords:
        keywords = [user_query]

    search_fields = {
        "coursera": ["Title", "Short Intro", "Skills", "Category"],
        "udacity": ["Title", "Short Intro", "What you learn"],
        "simplilearn": ["Title", "Short Intro", "Skills"],
        "futurelearn": ["Title", "Short Intro", "Category"],
    }
    fields_to_search = search_fields.get(provider, ["Title", "Short Intro"])

    fallback_conditions = []
    for keyword in keywords:
        for field in fields_to_search:
            condition = {field: {"$regex": keyword, "$options": "i"}}
            fallback_conditions.append(condition)

    if fallback_conditions:
        return {"$or": fallback_conditions}
    else:
        return {}


def generateQueriesUsingLLM(userQuery, schemas):
    """
    Generates MongoDB queries using the FIELD NAMES FROM THE SCHEMA.
    """
    prompt = f"""
You are an expert MongoDB query generator. Based on the user's query and the database schema below, generate a MongoDB query for each relevant provider.

**USER'S QUERY:** "{userQuery}"

**DATABASE SCHEMA (Use these exact field names in your queries):**
{json.dumps(schemas, indent=2)}

**INSTRUCTIONS:**
1.  For each provider (coursera, udacity, futurelearn, simplilearn), generate a query to find relevant courses.
2.  Use only the field names provided in the schema above.
3.  Use the `$regex` operator with `"$options": "i"` for case-insensitive text search.
4.  Use `$or` to search across multiple fields.
5.  **OUTPUT MUST BE A SINGLE JSON OBJECT.** The keys are provider names, the values are MongoDB query objects.

**Output ONLY the raw JSON. No other text.**
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    raw_text = (response.text or "").strip()
    print("\n--- Raw LLM Query Output (Using Schema Fields) ---\n", raw_text)

    parsed = _find_balanced_json(raw_text)
    if parsed is None:
        print("ERROR: Could not extract valid JSON from LLM response.")
        return {}
    return parsed


def translate_query_to_db_fields(query_obj, provider):
    """
    Recursively translates a query object from schema field names to real database field names.
    """
    translation_map = SCHEMA_TO_DB_FIELD_MAP.get(provider, {})
    translated_obj = {}

    for key, value in query_obj.items():
        if not key.startswith("$") and key in translation_map:
            new_key = translation_map[key]
        else:
            new_key = key

        if isinstance(value, dict):
            translated_obj[new_key] = translate_query_to_db_fields(value, provider)
        elif isinstance(value, list):
            translated_obj[new_key] = [
                (
                    translate_query_to_db_fields(item, provider)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]
        else:
            translated_obj[new_key] = value

    return translated_obj


def processUserQuery(userQuery):
    schemas = getSchemasAndSamples()

    generated_queries = generateQueriesUsingLLM(userQuery, schemas)
    print(
        "\n--- LLM Queries (Schema Fields) ---\n",
        json.dumps(generated_queries, indent=2),
    )

    all_results = []
    debug_info = {
        "user_query": userQuery,
        "llm_generated_queries_schema_fields": generated_queries,
        "llm_generated_queries_db_fields": {},
        "execution_results": {},
    }

    for provider, schema_field_query in generated_queries.items():
        provider_lower = provider.lower()
        db = dbMap.get(provider_lower)

        if db is None:
            print(f"Database for provider '{provider}' not configured. Skipping.")
            debug_info["execution_results"][provider] = {"error": "DB not configured"}
            continue

        collection_name = COLLECTION_MAP.get(provider_lower)
        coll = db.get_collection(collection_name)

        db_field_query = translate_query_to_db_fields(
            schema_field_query, provider_lower
        )
        debug_info["llm_generated_queries_db_fields"][provider] = db_field_query

        print(f"\n--- Executing for {provider} ---")
        print("Translated DB Query:", json.dumps(db_field_query, indent=2))

        final_query_used = db_field_query
        used_fallback = False
        execution_error = None

        try:
            cursor = coll.find(db_field_query)
            matched_docs = list(cursor)

            if len(matched_docs) == 0:
                print("Precise query found 0 results. Trying keyword fallback...")
                used_fallback = True
                fallback_query = build_keyword_fallback_query(userQuery, provider_lower)
                final_query_used = fallback_query
                print("Fallback Query:", json.dumps(fallback_query, indent=2))
                cursor = coll.find(fallback_query)
                matched_docs = list(cursor)

            print(f"Found {len(matched_docs)} matches.")
            sanitized_docs = [sanitize_doc(doc) for doc in matched_docs]

            debug_info["execution_results"][provider] = {
                "collection": collection_name,
                "query": final_query_used,
                "match_count": len(sanitized_docs),
                "used_fallback": used_fallback,
                "execution_error": execution_error,
            }

            for doc in sanitized_docs:
                all_results.append(
                    {
                        "provider": provider_lower,
                        "original_data": doc,
                        "unified_data": unifyResponse(provider_lower, doc),
                    }
                )

        except Exception as e:
            error_msg = f"Failed to execute query for {provider}: {str(e)}"
            print(error_msg)
            execution_error = error_msg
            debug_info["execution_results"][provider] = {
                "collection": collection_name,
                "query": final_query_used,
                "match_count": 0,
                "used_fallback": used_fallback,
                "execution_error": error_msg,
            }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(OUTPUT_DIR, f"responses_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(
            {"query": userQuery, "debug": debug_info, "results": all_results},
            fh,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n--- Process Complete. Results saved to {out_path} ---")
    return {"query": userQuery, "results": all_results, "debug": debug_info}
