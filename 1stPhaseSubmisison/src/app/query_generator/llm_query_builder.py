# src/app/query_generator/llm_query_builder.py
import json
import re
import google.generativeai as genai
import os
from src.app.schema_loader import getSchemasAndSamples

# Use your API key
API_KEY = "AIzaSyC7mkmr7MQP43NC-pzM_IMKi7nAeKIt6p0"
genai.configure(api_key=API_KEY)


def _find_balanced_json(text: str):
    """Extract JSON from LLM response"""
    if not text:
        return None

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


def generate_queries(user_query):
    """
    Generates intelligent MongoDB queries supporting both SPJ and Aggregate operations
    """
    schemas = getSchemasAndSamples()

    prompt = f"""
You are an expert MongoDB query generator for educational courses. Analyze the user's query and generate precise queries.

**USER'S QUERY:** "{user_query}"

**DATABASE SCHEMA:**
{json.dumps(schemas, indent=2)}

**QUERY TYPE DETECTION:**

1. **SPJ QUERIES (Select-Project-Join):**
   - Simple filtering: "Python courses", "DBMS courses from Coursera"
   - Field selection: "Show course titles and durations"
   - Multi-condition: "Beginner level Python courses with rating > 4.5"

2. **AGGREGATE QUERIES:**
   - **Sorting/Limiting**: "Top 5 most viewed courses", "Lowest price courses"
   - **Statistical**: "Average duration of Data Science courses", "Count of courses per category"
   - **Ranking**: "Highest rated courses per platform", "Most popular skills"
   - **Cross-platform aggregation**: "Overall top 10 courses from all platforms"

**QUERY CONSTRUCTION RULES:**

**For SPJ Queries:**
- Use $regex for text searches: "\\bPython\\b"
- Use $or for multiple field searches
- Use $and for combined conditions
- Use field projection to select specific fields

**For Aggregate Queries:**
- Use $sort for ordering
- Use $limit for top N results
- Use $match for filtering before aggregation
- For cross-platform queries, generate separate queries for each provider

**OUTPUT STRUCTURE:**
{{
  "query_type": "SPJ|AGGREGATE",
  "description": "Brief description of query intent",
  "providers": {{
    "coursera": {{ "query": {{...}} }},
    "udacity": {{ "query": {{...}} }},
    "simplilearn": {{ "query": {{...}} }},
    "futurelearn": {{ "query": {{...}} }}
  }}
}}

**EXAMPLES:**

**Example 1 - SPJ Query: "Python courses from Coursera and Udacity"**
{{
  "query_type": "SPJ",
  "description": "Filter Python courses from specific providers",
  "providers": {{
    "coursera": {{
      "$or": [
        {{"Skills Covered": {{"$regex": "\\bPython\\b", "$options": "i"}}}},
        {{"Course Title": {{"$regex": "\\bPython\\b", "$options": "i"}}}}
      ]
    }},
    "udacity": {{
      "$or": [
        {{"Skills Covered": {{"$regex": "\\bPython\\b", "$options": "i"}}}},
        {{"Course Title": {{"$regex": "\\bPython\\b", "$options": "i"}}}}
      ]
    }}
  }}
}}

**Example 2 - Aggregate Query: "Top 5 lowest cost Data Science courses from all platforms"**
{{
  "query_type": "AGGREGATE",
  "description": "Find cheapest Data Science courses across all platforms",
  "providers": {{
    "coursera": {{
      "$and": [
        {{
          "$or": [
            {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
            {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
          ]
        }},
        {{"$sort": {{"Price": 1}}}},
        {{"$limit": 5}}
      ]
    }},
    "udacity": {{
      "$and": [
        {{
          "$or": [
            {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
            {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
          ]
        }},
        {{"$sort": {{"Price": 1}}}},
        {{"$limit": 5}}
      ]
    }},
    "simplilearn": {{
      "$and": [
        {{
          "$or": [
            {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
            {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
          ]
        }},
        {{"$sort": {{"Price": 1}}}},
        {{"$limit": 5}}
      ]
    }},
    "futurelearn": {{
      "$and": [
        {{
          "$or": [
            {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
            {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
          ]
        }},
        {{"$sort": {{"Price": 1}}}},
        {{"$limit": 5}}
      ]
    }}
  }}
}}

**Example 3 - Complex Aggregate: "Most popular programming languages across all platforms"**
{{
  "query_type": "AGGREGATE", 
  "description": "Analyze programming language popularity across platforms",
  "providers": {{
    "coursera": {{
      "$match": {{
        "$or": [
          {{"Skills Covered": {{"$regex": "\\bPython\\b|\\bJava\\b|\\bJavaScript\\b|\\bC\\+\\+|\\bC#\\b", "$options": "i"}}}}
        ]
      }}
    }},
    "udacity": {{
      "$match": {{
        "$or": [
          {{"Skills Covered": {{"$regex": "\\bPython\\b|\\bJava\\b|\\bJavaScript\\b|\\bC\\+\\+|\\bC#\\b", "$options": "i"}}}}
        ]
      }}
    }},
    "simplilearn": {{
      "$match": {{
        "$or": [
          {{"Skills Covered": {{"$regex": "\\bPython\\b|\\bJava\\b|\\bJavaScript\\b|\\bC\\+\\+|\\bC#\\b", "$options": "i"}}}}
        ]
      }}
    }},
    "futurelearn": {{
      "$match": {{
        "$or": [
          {{"Skills Covered": {{"$regex": "\\bPython\\b|\\bJava\\b|\\bJavaScript\\b|\\bC\\+\\+|\\bC#\\b", "$options": "i"}}}}
        ]
      }}
    }}
  }}
}}

**NOW GENERATE FOR: "{user_query}"**

Return ONLY the JSON, no other text.
"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        raw_text = (response.text or "").strip()

        print(f"DEBUG: Raw LLM response: {raw_text[:300]}...")

        parsed = _find_balanced_json(raw_text)

        if parsed is None:
            print("ERROR: Could not extract valid JSON from LLM response.")
            return {}

        return parsed

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {}
