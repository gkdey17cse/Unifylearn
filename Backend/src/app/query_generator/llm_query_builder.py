# src/app/query_generator/llm_query_builder.py
import json
import re
import time
import random
import google.generativeai as genai
import os
from src.app.schema_loader import getSchemasAndSamples
from src.app.utils.logger import logger

# Configure Gemini with rate limiting
last_request_time = 0


def _enforce_rate_limit():
    global last_request_time
    current_time = time.time()
    time_since_last_request = current_time - last_request_time

    if time_since_last_request < 3.0:
        sleep_time = 3.0 - time_since_last_request
        time.sleep(sleep_time)

    last_request_time = time.time()


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


def call_gemini_with_retry(prompt, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            _enforce_rate_limit()
            logger.llm(f"Calling Gemini API (attempt {attempt + 1}/{max_retries + 1})")

            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            if response.text:
                return response.text
            else:
                raise ValueError("Empty response from Gemini")

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg and attempt < max_retries:
                wait_time = (2**attempt) + random.uniform(1, 3)
                time.sleep(wait_time)
            else:
                raise e

    return None


def generate_queries(user_query):
    logger.query(f"Processing: '{user_query}'")

    schemas = getSchemasAndSamples()

    prompt = f"""
You are an expert MongoDB query generator for educational courses. Analyze the user's query and generate precise queries.

**USER'S QUERY:** "{user_query}"

**DATABASE SCHEMA:**
{json.dumps(schemas, indent=2)}

**CRITICAL FIELD MAPPING - Use these EXACT field names:**
- For ALL providers: Use "Title", "Short Intro", "Category", "Number of viewers"
- For Coursera: Use "Skills", "Sub-Category", "Rating"  
- For Udacity: Use "What you learn", "Level", "Program Type"
- For Simplilearn: Use "Skills", "Course Type"
- For FutureLearn: Use "Sub-Category", "Duration"

**QUERY TYPE DETECTION:**
- SPJ: Simple filtering like "Python courses", "AI courses from Coursera", "Law courses"
- AGGREGATE: Queries with sorting, limiting, ranking like "top 5", "most viewed", "highest rated"

**OUTPUT STRUCTURE:**
{{
  "query_type": "SPJ|AGGREGATE",
  "description": "Brief description",
  "aggregation_strategy": "provider_level|cross_platform",
  "sort_field": "Number of viewers|Rating", 
  "sort_order": 1|-1,
  "global_limit": 5,
  "providers": {{
    "coursera": {{...query...}},
    "udacity": {{...query...}},
    "simplilearn": {{...query...}},
    "futurelearn": {{...query...}}
  }}
}}

**EXAMPLES:**

**"Law courses from Coursera" (SPJ query):**
{{
  "query_type": "SPJ",
  "description": "Law courses from Coursera",
  "aggregation_strategy": "provider_level",
  "providers": {{
    "coursera": {{
      "$or": [
        {{"Title": {{"$regex": "\\\\bLaw\\\\b", "$options": "i"}}}},
        {{"Category": {{"$regex": "\\\\bLaw\\\\b", "$options": "i"}}}},
        {{"Sub-Category": {{"$regex": "\\\\bLaw\\\\b", "$options": "i"}}}}
      ]
    }},
    "udacity": {{}},
    "simplilearn": {{}},
    "futurelearn": {{}}
  }}
}}

**"Python courses for beginners" (SPJ query):**
{{
  "query_type": "SPJ", 
  "description": "Python beginner courses",
  "aggregation_strategy": "provider_level",
  "providers": {{
    "coursera": {{
      "$and": [
        {{"$or": [
          {{"Title": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}},
          {{"Skills": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}}
        ]}},
        {{"$or": [
          {{"Course Type": {{"$regex": "\\\\bBeginner\\\\b", "$options": "i"}}}},
          {{"Level": {{"$regex": "\\\\bBeginner\\\\b", "$options": "i"}}}}
        ]}}
      ]
    }},
    "udacity": {{
      "$and": [
        {{"$or": [
          {{"Title": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}},
          {{"What you learn": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}}
        ]}},
        {{"Level": {{"$regex": "\\\\bBeginner\\\\b", "$options": "i"}}}}
      ]
    }},
    "simplilearn": {{
      "$and": [
        {{"$or": [
          {{"Title": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}},
          {{"Skills": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}}
        ]}},
        {{"Course Type": {{"$regex": "\\\\bBeginner\\\\b", "$options": "i"}}}}
      ]
    }},
    "futurelearn": {{
      "$and": [
        {{"$or": [
          {{"Title": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}},
          {{"Category": {{"$regex": "\\\\bPython\\\\b", "$options": "i"}}}}
        ]}},
        {{"Level": {{"$regex": "\\\\bBeginner\\\\b", "$options": "i"}}}}
      ]
    }}
  }}
}}

**"Top 5 most viewed courses from all platforms":**
{{
  "query_type": "AGGREGATE",
  "description": "Top 5 most viewed courses across all platforms",
  "aggregation_strategy": "cross_platform", 
  "sort_field": "Number of viewers",
  "sort_order": -1,
  "global_limit": 5,
  "providers": {{
    "coursera": {{}},
    "udacity": {{}},
    "simplilearn": {{}},
    "futurelearn": {{}}
  }}
}}

**"Machine Learning courses sorted by number of viewers":**
{{
  "query_type": "AGGREGATE", 
  "description": "Machine Learning courses sorted by viewers",
  "aggregation_strategy": "cross_platform",
  "sort_field": "Number of viewers",
  "sort_order": -1,
  "providers": {{
    "coursera": {{
      "$or": [
        {{"Title": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}},
        {{"Category": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}}
      ]
    }},
    "udacity": {{
      "$or": [
        {{"Title": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}},
        {{"What you learn": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}}
      ]
    }},
    "simplilearn": {{
      "$or": [
        {{"Title": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}},
        {{"Skills": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}}
      ]
    }},
    "futurelearn": {{
      "$or": [
        {{"Title": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}},
        {{"Category": {{"$regex": "\\\\bMachine Learning\\\\b", "$options": "i"}}}}
      ]
    }}
  }}
}}

**NOW GENERATE FOR: "{user_query}"**

Return ONLY the JSON, no other text.
"""

    try:
        raw_text = call_gemini_with_retry(prompt)

        if not raw_text:
            logger.warning("Empty response from Gemini")
            return {"query_type": "SPJ", "providers": {}}

        parsed = _find_balanced_json(raw_text)

        if parsed is None:
            logger.warning("Could not parse JSON from LLM response")
            return {"query_type": "SPJ", "providers": {}}

        logger.success("Generated queries successfully")
        return parsed

    except Exception as e:
        logger.error(f"Gemini query generation failed: {e}")
        return {"query_type": "SPJ", "providers": {}}