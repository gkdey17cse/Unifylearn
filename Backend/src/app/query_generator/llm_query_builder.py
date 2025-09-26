import json
import re
import google.generativeai as genai
import os
from src.app.schema_loader import getSchemasAndSamples

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


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

**QUERY GENERATION STRATEGY:**

1. **PROVIDER SELECTION:**
   - If specific providers are mentioned (Coursera, Udacity, etc.), ONLY generate for those
   - If no provider specified, generate for all relevant providers

2. **QUERY TYPE DETECTION:**
   - **Category-based:** "Law courses", "Data Science programs" → Use "Main Category" and "Sub-Category"
   - **Technology-based:** ".Net development", "Python courses" → Use "Skills Covered" and "Course Title"  
   - **Topic-based:** "Machine learning", "Web development" → Use "Brief Description" and "Skills Covered"
   - **Mixed queries:** Handle combinations intelligently

3. **FIELD SELECTION GUIDELINES:**
   - For categories: ["Main Category", "Sub-Category"]
   - For technologies: ["Skills Covered", "Course Title"] 
   - For general topics: ["Brief Description", "Skills Covered"]
   - For course names: ["Course Title"] (exact match preferred)

4. **QUERY CONSTRUCTION:**
   - Use word boundaries: "\\bLaw\\b" instead of "Law"
   - Preserve technical phrases: "\\b.Net development\\b" not separate words
   - Use $and for must-have conditions, $or for alternatives
   - Include $limit for numeric requests: "5 courses" → "$limit": 5

5. **EXAMPLES:**

**Query: "Show me 5 Coursera courses in Data Science"**
{{
  "coursera": {{
    "$and": [
      {{
        "$or": [
          {{"Main Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}},
          {{"Sub-Category": {{"$regex": "\\bData Science\\b", "$options": "i"}}}}
        ]
      }},
      {{"$limit": 5}}
    ]
  }}
}}

**Query: ".Net development courses on Udacity"**
{{
  "udacity": {{
    "$and": [
      {{
        "$or": [
          {{"Skills Covered": {{"$regex": "\\b\\.Net\\b", "$options": "i"}}}},
          {{"Skills Covered": {{"$regex": "\\bC#\\b", "$options": "i"}}}},
          {{"Course Title": {{"$regex": "\\b\\.Net\\b", "$options": "i"}}}}
        ]
      }}
    ]
  }}
}}

**Query: "Law courses from all platforms"**
{{
  "coursera": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Skills Covered": {{"$regex": "\\bLaw\\b", "$options": "i"}}}}
    ]
  }},
  "udacity": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Skills Covered": {{"$regex": "\\bLaw\\b", "$options": "i"}}}}
    ]
  }},
  "futurelearn": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Skills Covered": {{"$regex": "\\bLaw\\b", "$options": "i"}}}}
    ]
  }},
  "simplilearn": {{
    "$or": [
      {{"Main Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Sub-Category": {{"$regex": "\\bLaw\\b", "$options": "i"}}}},
      {{"Skills Covered": {{"$regex": "\\bLaw\\b", "$options": "i"}}}}
    ]
  }}
}}

**Output ONLY the raw JSON. No other text.**
"""
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt)
    raw_text = (response.text or "").strip()
    print("\n--- Raw LLM Query Output (Using Schema Fields) ---\n", raw_text)

    parsed = _find_balanced_json(raw_text)
    if parsed is None:
        print("ERROR: Could not extract valid JSON from LLM response.")
        return {}
    return parsed
