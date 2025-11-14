# src/app/query_generator/llm_query_builder.py
import json
import re
import time
import random
import google.generativeai as genai
import os
from src.app.schema_loader import getSchemasAndSamples

# Configure Gemini with rate limiting
last_request_time = 0

def _enforce_rate_limit():
    """Enforce rate limiting between requests"""
    global last_request_time
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    
    if time_since_last_request < 3.0:  # 3 second minimum between requests
        sleep_time = 3.0 - time_since_last_request
        print(f"⏳ Rate limiting: Waiting {sleep_time:.1f} seconds...")
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
    """Call Gemini API with retry logic"""
    for attempt in range(max_retries + 1):
        try:
            _enforce_rate_limit()
            print(f"🤖 Calling Gemini API (attempt {attempt + 1}/{max_retries + 1})...")
            
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            
            if response.text:
                return response.text
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  API attempt {attempt + 1} failed: {error_msg}")
            
            if "429" in error_msg and attempt < max_retries:
                wait_time = (2 ** attempt) + random.uniform(1, 3)
                print(f"🕒 Rate limit hit. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                raise e
    
    return None

def generate_fallback_queries(user_query):
    """Fallback when Gemini fails"""
    print("🔄 Using intelligent fallback query generator...")
    
    providers = ["coursera", "udacity", "simplilearn", "futurelearn"]
    
    # Extract keywords and limit
    words = re.findall(r'\b[a-zA-Z0-9+#\.]{2,}\b', user_query.lower())
    stopwords = {
        'show', 'me', 'all', 'from', 'any', 'platform', 'only', 'related', 
        'course', 'courses', 'program', 'programs', 'get', 'find', 'search'
    }
    
    # Extract numeric limit
    limit_match = re.search(r'\b(\d+)\s+courses?\b', user_query.lower())
    limit_value = int(limit_match.group(1)) if limit_match else None
    
    keywords = [word for word in words if word not in stopwords and len(word) > 2 and not word.isdigit()]
    
    # Provider detection
    mentioned_providers = []
    for provider in providers:
        if provider in user_query.lower():
            mentioned_providers.append(provider)
    
    target_providers = mentioned_providers if mentioned_providers else providers
    
    queries = {}
    for provider in target_providers:
        if keywords:
            search_conditions = []
            for keyword in keywords[:4]:  # Use more keywords for better matching
                # Use actual database field names in fallback
                if provider == "coursera":
                    search_conditions.extend([
                        {"Title": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Short Intro": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Skills": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Category": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}}
                    ])
                elif provider == "udacity":
                    search_conditions.extend([
                        {"Title": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Short Intro": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"What you learn": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}}
                    ])
                elif provider == "simplilearn":
                    search_conditions.extend([
                        {"Title": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Short Intro": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Skills": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}}
                    ])
                elif provider == "futurelearn":
                    search_conditions.extend([
                        {"Title": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Short Intro": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}},
                        {"Category": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}}
                    ])
            
            base_query = {"$or": search_conditions}
            if limit_value:
                base_query["$limit"] = limit_value
                
            queries[provider] = base_query
        else:
            base_query = {"Title": {"$regex": ".*", "$options": "i"}}
            if limit_value:
                base_query["$limit"] = limit_value
            queries[provider] = base_query
    
    return queries

def generate_queries(user_query):
    """
    Generates intelligent MongoDB queries with comprehensive error handling
    """
    print(f"🔍 Processing query: '{user_query}'")
    
    schemas = getSchemasAndSamples()

    prompt = f"""
You are an expert MongoDB query generator for educational courses. Analyze the user's query and generate precise queries.

**USER'S QUERY:** "{user_query}"

**DATABASE SCHEMA (Use these EXACT field names in your queries):**
{json.dumps(schemas, indent=2)}

**IMPORTANT INSTRUCTIONS:**

1. **USE ACTUAL DATABASE FIELD NAMES** from the schema above
2. **For limits:** Use "$limit" at the top level or in $and conditions
3. **For searching:** Use "$regex" with word boundaries like "\\bPython\\b"
4. **For multiple fields:** Use "$or" to search across relevant fields

**QUERY EXAMPLES:**

**Example 1: "Show 3 Python courses from Coursera"**
{{
  "coursera": {{
    "$or": [
      {{"Title": {{"$regex": "\\bPython\\b", "$options": "i"}}}},
      {{"Short Intro": {{"$regex": "\\bPython\\b", "$options": "i"}}}},
      {{"Skills": {{"$regex": "\\bPython\\b", "$options": "i"}}}}
    ],
    "$limit": 3
  }}
}}

**Example 2: "Database courses from all platforms"**
{{
  "coursera": {{
    "$or": [
      {{"Title": {{"$regex": "\\bDatabase\\b", "$options": "i"}}}},
      {{"Short Intro": {{"$regex": "\\bDatabase\\b", "$options": "i"}}}},
      {{"Skills": {{"$regex": "\\bDatabase\\b", "$options": "i"}}}}
    ]
  }},
  "udacity": {{
    "$or": [
      {{"Title": {{"$regex": "\\bDatabase\\b", "$options": "i"}}}},
      {{"Short Intro": {{"$regex": "\\bDatabase\\b", "$options": "i"}}}},
      {{"What you learn": {{"$regex": "\\bDatabase\\b", "$options": "i"}}}}
    ]
  }}
}}

**NOW GENERATE FOR: "{user_query}"**

Return ONLY the JSON, no other text.
"""

    try:
        raw_text = call_gemini_with_retry(prompt)
        
        if not raw_text:
            print("❌ Empty response from Gemini, using fallback")
            return generate_fallback_queries(user_query)

        print(f"📨 Raw LLM response received ({len(raw_text)} chars)")
        
        parsed = _find_balanced_json(raw_text)

        if parsed is None:
            print("❌ Could not parse JSON from LLM response. Using fallback.")
            return generate_fallback_queries(user_query)

        print("✅ Successfully generated queries with Gemini")
        return parsed

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Gemini query generation failed: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower():
            print("💡 Tip: API limits reached. Using fallback mode.")
            time.sleep(2)
        else:
            print("🌐 API unavailable. Using fallback mode.")
            
        return generate_fallback_queries(user_query)