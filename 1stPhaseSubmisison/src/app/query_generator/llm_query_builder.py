# src/app/query_generator/llm_query_builder.py
import json
import re
import google.generativeai as genai
import os
from src.app.schema_loader import getSchemasAndSamples

# TEMPORARY: Hardcode API key for testing
API_KEY = "AIzaSyCZA-_semc7d5ogZsN7wkKzKXGXTsk0dvw"
genai.configure(api_key=API_KEY)


def _find_balanced_json(text: str):
    """Extract JSON from LLM response more robustly"""
    if not text:
        return None

    # Remove code blocks if present
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

    # Try to find JSON object
    starts = [i for i, c in enumerate(text) if c == "{"]
    candidates = []

    for i in starts:
        depth = 0
        in_string = False
        escape = False
        for j in range(i, len(text)):
            char = text[j]

            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == '"' and not escape:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[i : j + 1])
                        break

    # Try candidates from longest to shortest
    candidates.sort(key=len, reverse=True)

    for cand in candidates:
        try:
            parsed = json.loads(cand)
            # Ensure it's a dictionary with provider keys
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue

    return None


def generate_queries(user_query):
    """
    Generates intelligent MongoDB queries based on user intent.
    """
    schemas = getSchemasAndSamples()

    prompt = f"""
You are an expert MongoDB query generator for educational courses. Analyze the user's query and generate precise, context-aware queries.

**USER'S QUERY:** "{user_query}"

**DATABASE SCHEMA (Use these exact field names in your queries):**
{json.dumps(schemas, indent=2)}

**QUERY GENERATION RULES:**

1. **PROVIDER SELECTION:**
   - If specific providers are mentioned (Coursera, Udacity, Simplilearn, FutureLearn), ONLY generate for those
   - If no provider specified, generate for ALL four providers

2. **QUERY CONSTRUCTION:**
   - For technology/topic searches (like "DBMS", "Python", "Machine Learning"), search in: ["Skills Covered", "Course Title", "Brief Description"]
   - For category searches (like "Data Science", "Business"), search in: ["Main Category", "Sub-Category"]
   - Use $regex with word boundaries for better matching
   - Use $or for multiple field searches
   - Use $and for combined conditions

3. **OUTPUT FORMAT:**
   - Return ONLY a valid JSON object
   - Keys must be provider names in lowercase: "coursera", "udacity", "simplilearn", "futurelearn"
   - Values must be MongoDB query objects

**EXAMPLES:**

Query: "Show me DBMS courses from Simplilearn & Udacity"
{{
  "simplilearn": {{
    "$or": [
      {{"Skills Covered": {{"$regex": "\\bDBMS\\b", "$options": "i"}}}},
      {{"Course Title": {{"$regex": "\\bDBMS\\b", "$options": "i"}}}},
      {{"Brief Description": {{"$regex": "\\bDBMS\\b", "$options": "i"}}}}
    ]
  }},
  "udacity": {{
    "$or": [
      {{"Skills Covered": {{"$regex": "\\bDBMS\\b", "$options": "i"}}}},
      {{"Course Title": {{"$regex": "\\bDBMS\\b", "$options": "i"}}}},
      {{"Brief Description": {{"$regex": "\\bDBMS\\b", "$options": "i"}}}}
    ]
  }}
}}

Query: "Data Science courses from all platforms"
{{
  "coursera": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
    ]
  }},
  "udacity": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
    ]
  }},
  "simplilearn": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
    ]
  }},
  "futurelearn": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
    ]
  }}
}}

**NOW GENERATE FOR THIS QUERY: "{user_query}"**

Return ONLY the JSON, no other text.
"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)
        raw_text = (response.text or "").strip()

        print(f"DEBUG: Raw LLM response: {raw_text[:500]}...")  # Print first 500 chars

        parsed = _find_balanced_json(raw_text)

        if parsed is None:
            print("ERROR: Could not extract valid JSON from LLM response.")
            print(f"Full response: {raw_text}")
            return {}

        print(f"DEBUG: Successfully parsed JSON with keys: {list(parsed.keys())}")
        return parsed

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {}
