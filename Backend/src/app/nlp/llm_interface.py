# src/app/nlp/llm_interface.py
import json
import logging
from typing import Dict, List, Any, Optional

# import your LLM client here (example uses 'client' as before)
# from google import genai
# client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# keep the existing analyzer you already had
def analyze_query_with_llm(query: str) -> dict:
    """
    Sends the user query to Google Gemini for analysis and structured interpretation.
    Returns a free-form llm_output (text), used for logging/UI rather than direct execution.
    """
    prompt = f"""
    Analyze the following user query and break it down into:
    - Intent
    - Relevant keywords
    - Suggested database(s)
    - Possible filters or constraints

    Query: "{query}"
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-pro", contents=[{"role": "user", "parts": [prompt]}]
        )
        return {"raw": query, "llm_output": getattr(response, "text", str(response))}
    except Exception as e:
        logging.exception("LLM analyze error")
        return {"raw": query, "error": str(e)}


# New: Generate executable MongoDB plans from user query + schema
def generate_mongo_queries_with_llm(
    user_query: str, providers_schema: Dict[str, Dict[str, Any]], max_per_provider: int = 50
) -> Optional[List[Dict[str, Any]]]:
    """
    Ask the LLM to produce executable MongoDB 'plans' (JSON) for each provider.
    providers_schema should be the PROVIDERS map from plan_builder, e.g.:
        {
           "coursera": {"db": "...", "coll": "...", "text_fields": [...]},
           ...
        }
    The LLM MUST return strict JSON in the exact format described in the prompt below.
    We validate the returned JSON and sanitize fields before returning it to the caller.

    Returns:
        list of plans OR None if generation/validation failed.
    """
    # Create a concise schema description for the prompt
    schema_snippets = []
    for pname, meta in providers_schema.items():
        fields = meta.get("text_fields", [])
        schema_snippets.append(
            json.dumps({"provider": pname, "db": meta.get("db"), "coll": meta.get("coll"), "fields": fields})
        )
    schema_block = "\n".join(schema_snippets)

    # Prompt: demand strict JSON array output with only allowed structure
    prompt = f"""
You are given:
1) A user natural-language query: {json.dumps(user_query)}
2) Database schema information (providers and their collections & searchable fields):
{schema_block}

Task:
Produce a JSON array of "plans", one per provider that should be queried.
Each plan MUST be an object with these keys:
- provider: <provider key matching the schema (e.g., 'coursera')>
- db: <database name (string)>
- coll: <collection name (string)>
- filter: <a MongoDB-style JSON object used as the find() filter; use $regex for text matches>
- projection: <a JSON object of fields to return with 1/0, or null to use default projection>
- limit: <integer, number of documents to request from this provider; must be <= {max_per_provider}>

Important instructions for the LLM output:
- Return ONLY valid JSON (no surrounding commentary). The top-level value must be a JSON array.
- Use case-sensitive field names exactly as provided in the schema when referencing fields.
- If a provider is not relevant to the query, do not include it in the array.
- For text search, prefer $or + $regex on the fields provided in the schema
- Keep the limit conservative; do not exceed {max_per_provider} per provider.

Example single-plan structure:
{{
  "provider": "coursera",
  "db": "CourseraDB",
  "coll": "Coursera",
  "filter": {{"$or":[{{"Title":{{"$regex":"Python","$options":"i"}}}}]}},
  "projection": {{"Title":1, "URL":1, "Short Intro":1}},
  "limit": 5
}}

Return only the JSON array.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-pro", contents=[{"role": "user", "parts": [prompt]}], temperature=0.0
        )
        raw_text = getattr(response, "text", str(response))
    except Exception as e:
        logging.exception("LLM plan generation failed")
        return None

    # Attempt to extract / parse JSON from the LLM output
    try:
        # Many LLMs sometimes wrap JSON in backticks or code fences; try to find the first JSON array
        start = raw_text.find("[")
        end = raw_text.rfind("]") + 1
        json_text = raw_text[start:end] if start != -1 and end != -1 else raw_text
        plans = json.loads(json_text)
    except Exception:
        logging.exception("Failed to parse JSON from LLM output: %s", raw_text)
        return None

    # Validate and sanitize each plan
    validated_plans = []
    allowed_providers = set(providers_schema.keys())
    for p in plans:
        try:
            provider = p.get("provider")
            db = p.get("db")
            coll = p.get("coll")
            filt = p.get("filter", {}) or {}
            proj = p.get("projection", None)
            limit = int(p.get("limit", max_per_provider))

            # Basic checks
            if provider not in allowed_providers:
                logging.warning("LLM returned unknown provider: %s", provider)
                continue
            schema_meta = providers_schema[provider]
            # ensure db/coll match expected (if they provided different names, override with schema)
            if db != schema_meta.get("db"):
                logging.info("Overriding db from LLM for provider %s -> %s", provider, schema_meta.get("db"))
                db = schema_meta.get("db")
            if coll != schema_meta.get("coll"):
                logging.info("Overriding coll from LLM for provider %s -> %s", provider, schema_meta.get("coll"))
                coll = schema_meta.get("coll")

            # Enforce limit bounds
            if limit <= 0:
                limit = 1
            limit = min(limit, max_per_provider)

            # Sanitize filter: ensure the LLM only references known fields (very simple check)
            allowed_fields = set(schema_meta.get("text_fields", []))
            # Flatten textual occurrences of field names in filter JSON to find unknown refs (best-effort)
            filter_str = json.dumps(filt)
            # If filter references unknown field strings, reject this plan
            unknown_fields = []
            # Check for any quoted keys in the filter and verify they're in allowed_fields or common control keys
            try:
                # parse nested dict keys
                def collect_keys(obj, keys_set):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            keys_set.add(k)
                            collect_keys(v, keys_set)
                    elif isinstance(obj, list):
                        for it in obj:
                            collect_keys(it, keys_set)

                keys_found = set()
                collect_keys(filt, keys_found)
                # allow Mongo operators like $or, $and, $regex, $options
                mongo_ops = {k for k in keys_found if isinstance(k, str) and k.startswith("$")}
                candidate_fields = {k for k in keys_found if k not in mongo_ops}
                for cf in candidate_fields:
                    if cf not in allowed_fields:
                        unknown_fields.append(cf)
            except Exception:
                # if anything goes wrong with key collection, be conservative and skip validation here
                unknown_fields = []

            if unknown_fields:
                logging.warning("LLM plan for %s references unknown fields: %s", provider, unknown_fields)
                continue

            # projection validation: if provided ensure keys are in allowed fields
            if proj is not None:
                if not isinstance(proj, dict):
                    logging.warning("Projection for %s is not an object; ignoring projection", provider)
                    proj = None
                else:
                    proj_keys = set(proj.keys())
                    if not proj_keys.issubset(set(allowed_fields) | {"_id"}):
                        # drop unknown projection keys (but allow proven safe ones)
                        proj = {k: v for k, v in proj.items() if k in allowed_fields or k == "_id"}

            # All validation passed for this plan -> append canonicalized plan
            validated_plans.append(
                {
                    "provider": provider,
                    "db": db,
                    "coll": coll,
                    "filter": filt,
                    "projection": proj,
                    "limit": limit,
                }
            )
        except Exception:
            logging.exception("Error validating a plan item: %s", p)
            continue

    if not validated_plans:
        logging.warning("No valid plans produced by LLM")
        return None

    return validated_plans
