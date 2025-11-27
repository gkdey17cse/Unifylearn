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
    # Strip markdown code blocks
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

    # Try to find the largest outer bracket pair
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Fallback to stack method if regex fails
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
            # logger.llm(f"Calling Gemini API (attempt {attempt + 1}/{max_retries + 1})") # Optional logging

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

    # We reduce the schema complexity for the prompt to save tokens and reduce confusion
    simplified_schemas = {k: {"fields": v["fields"]} for k, v in schemas.items()}

#     prompt = f"""
#     You are a Principal Database Engineer. Your goal is to convert a user's natural language request into a **Semantic MongoDB Query**.
# # 
#     **USER QUERY:** "{user_query}"
# # 
#     ### 🧠 STEP 1: SEMANTIC EXPANSION (CRITICAL)
#     You MUST expand the user's terms into a broader list of synonyms.
#     # 
#     * **IF "AI"**: Expand to -> `(AI|Artificial Intelligence|Machine Learning|Deep Learning|Neural Networks|NLP)`
#     * **IF "Cyber Security"**: Expand to -> `(Cyber Security|Cybersecurity|Network Security|Ethical Hacking|InfoSec|Penetration Testing)`
#     * **IF "Web Dev"**: Expand to -> `(Web Development|HTML|CSS|JavaScript|React|Full Stack|Frontend|Backend)`
#     * **IF "Data Science"**: Expand to -> `(Data Science|Data Analysis|Statistics|Big Data|Pandas|Python)`
# # 
#     ### 🛠️ STEP 2: QUERY CONSTRUCTION
#     Construct a JSON object using MongoDB operators.
#     # 
#     1.  **Use Regex Groups:** Instead of multiple `$or` conditions for synonyms, use a single Regex Group joined by `|`.
#         * *BAD:* `{{ "$or": [ {{ "Title": "AI" }}, {{ "Title": "ML" }} ] }}`
#         * *GOOD:* `{{ "Title": {{ "$regex": "\\\\b(AI|ML|Deep Learning)\\\\b", "$options": "i" }} }}`
#     # 
#     2.  **Target Fields:** Search in `Title`, `Short Intro`, `Skills`, `Category`, `What you learn`.
#     # 
#     3.  **Strict Filtering:** If the user specifies "Beginner", "Free", or "Short", use `$and` to ensure those conditions are met alongside the semantic search.
#     # 
#     4. keep your mind our query also need to be platform specific , if user has mentioned I need course from particular platform like coursera or simplilearn , our query must be generated for that specified platform only , not for all platform . 
#     5. If it is not mentioned then we need to fetch data from all 4 pltform that we have , and we need to write query for all platform
# # 
#     ### 📝 TARGET SCHEMAS (Use these exact field names)
#     {json.dumps(simplified_schemas, indent=2)}
# # 
#     ### ✅ REQUIRED OUTPUT FORMAT
#     Return valid JSON only.
# # 
#     {{
#       "query_type": "SPJ",
#       "thought_process": "User asked for 'Cyber Security'. Expanding to include: Cybersecurity, Ethical Hacking, InfoSec, Network Security.",
#       "expanded_terms": ["Cyber Security", "Cybersecurity", "Ethical Hacking", "InfoSec", "Network Security"],
#       "providers": {{
#         "coursera": {{
#           "$or": [
#             {{ "Title": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }},
#             {{ "Skills": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }}
#           ]
#         }},
#         "udacity": {{
#            "$or": [
#             {{ "Title": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }},
#             {{ "What you learn": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }}
#           ]
#         }}
#         // ... Generate for simplilearn and futurelearn similarly
#       }}
#     }}
#     """


    prompt = f"""
    You are a Principal Database Engineer. Your goal is to convert a user's natural language request into a **Semantic MongoDB Query**.
    
    **USER QUERY:** "{user_query}"
    
    ### 🧠 STEP 1: SEMANTIC EXPANSION (CRITICAL)
    You need to expand the user's terms into a broader list of synonyms as the database may have stored things differently or may not have exact matches, but we will try to figure out relevant topics.
    #
    * **IF "AI"**: Expand to -> `(AI|Artificial Intelligence|Machine Learning|Deep Learning|Neural Networks|NLP|CV|Computer Vision etc....)`
    * **IF "Cyber Security"**: Expand to -> `(Cyber Security|Cybersecurity|Network Security|Ethical Hacking|InfoSec|Penetration Testing etc....)`
    * **IF "Web Dev"**: Expand to -> `(Web Development|HTML|CSS|JavaScript|React|Full Stack|Frontend|Backend etc.....)`
    * **IF "Data Science"**: Expand to -> `(Data Science|Data Analysis|Statistics|Big Data|Pandas|Python etc ...)`
    * like this see the domain and expand it with your intelligence
    
    #
    
    ### 🛠️ STEP 2: QUERY CONSTRUCTION
    Construct a JSON object using MongoDB operators.
    
    1. **Use Regex Groups:** Instead of multiple `$or` conditions for synonyms, use a single Regex Group joined by `|`.
        * *BAD:* `{{ "$or": [ {{ "Title": "AI" }}, {{ "Title": "ML" }} ] }}`
        * *GOOD:* `{{ "Title": {{ "$regex": "\\\\b(AI|ML|Deep Learning)\\\\b", "$options": "i" }} }}`
    
    #
    2. **Target Fields:** Search in `Title`, `Short Intro`, `Skills`, `Category`, `What you learn`. For your understanding, I am sharing some data for each database.
    
    a) Coursera DB's data
    {{
    "_id": {{ "$oid": "68aa13e9b82e4c212546608a" }},
    "Title": "PostgreSQL for Everybody Specialization",
    "URL": "https://www.coursera.org/specializations/postgresql-for-everybody",
    "Short Intro": "SQL: From Basic to Advanced. Learn SQL skills you can use in an actual, real-world environment",
    "Category": "Computer Science",
    "Sub-Category": "Mobile and Web Development",
    "Course Type": "Specialization",
    "Language": "English",
    "Subtitle Languages": "Subtitles: English",
    "Skills": "Json, Database (DBMS), Natural Language Processing, SQL, ",
    "Instructors": "Charles Russell Severance ,",
    "Rating": "4.7stars",
    "Number of viewers": "803",
    "Duration": "Approximately 4 months to complete",
    "Site": "Coursera"
    }}
    
    b) FutureLearn Database Data
    {{
    "_id": {{ "$oid": "68ac020e69e0bdd621a8c4bf" }},
    "Title": "Computer Science Essentials: Data Structures",
    "URL": "https://www.futurelearn.com/courses/computer-science-essentials-data-structures",
    "Short Intro": "Improve your data handling and organisation knowledge by learning the fundamentals of data structure.",
    "Duration": "3 weeks",
    "Site": "Future Learn",
    "Courses": "42 Courses",
    "Topics related to CRM": "AI & Robotics / Business Technology / Coding & Programming / CRM / Cyber Security / Data Analytics / Data Science / Data Visualisation / Django / Excel / Java / Machine Learning / Python / R Programming / Statistics / Tableau / Web Analytics etc...",
    "ExpertTracks": "11 ExpertTracks",
    "Course Title": "Computer Science Essentials: Data Structures",
    "Course URL": "https://www.futurelearn.com/courses/computer-science-essentials-data-structures",
    "Course Short Intro": "Improve your data handling and organisation knowledge by learning the fundamentals of data structure.",
    "Weekly study": "3 hours",
    "Premium course": "$84"
    }}
    
    c) Simplilearn database data
    {{
    "_id": {{ "$oid": "68ac04f569e0bdd621a8d7ae" }},
    "Title": "Gain Your Data Analytics Certificate With Purdue And IBM",
    "Short Intro": "Boost your career with this Data Analytics Program, in partnership with Purdue University & in collaboration with IBM, which features master classes and follows an applied learning model designed with real-life projects and business case studies.",
    "Category": "Simplilearn",
    "Subtitle Languages": "University Program",
    "Skills": 757,
    "Instructors": "Data Science & Business Analytics",
    "URL": "https://www.simplilearn.com/pgp-data-analytics-certification-training-course?tag="
    }}
    
    d) Udacity database data
    {{
    "_id": {{ "$oid": "68ac0cf969e0bdd621a8d861" }},
    "Title": "What is Programming?",
    "URL": "https://www.udacity.com/course/what-is-programming--ud994",
    "Short Intro": "A Coding Dictionary",
    "Duration": "Estimated timeApprox. 1 Day",
    "Site": "Udacity",
    "Program Type": "Free Course",
    "Level": "Beginner",
    "Prerequisites": "No prerequisites. See the Technology Requirements for using Udacity.",
    "What you learn": "Web Development LanguagesLearn how to explain and categorize web development languages.Learn how to explain and categorize web development languages. ProgrammingExperience what \"programming\" is like by looking at what a developer does every day.Experience what \"programming\" is like by looking at what a developer does every day. StandardsLearn the lingo related to what web standards are and how programming languages are developedLearn the lingo related to what web standards are and how programming languages are developedVersion ControlGet familiar with what Version Control is, how it works, and what related tools are used.Get familiar with what Version Control is, how it works, and what related tools are used.Disparate Web TermsLearn a variety of disparate web terms and how they work together in the digital world.Learn a variety of disparate web terms and how they work together in the digital world."
    }}
    
    3. **Strict Filtering:** If the user specifies "Beginner", "Free", or "Short", use `$and` to ensure those conditions are met alongside the semantic search.
    
    4. Keep in mind: query must be **platform specific**. If the user mentions Coursera or Simplilearn, generate only for those platforms. Examples:
    a) I need DB course from Coursera & Simplilearn → generate query only for Coursera & Simplilearn  
    b) I need Machine Learning or AWS courses → generate nested queries for all platforms  
    c) Show me AI course from Simplilearn, C++ course from Coursera, Web Development course from FutureLearn, Business & Law course from Udacity → generate asymmetric queries per platform
    
    5. If no platform is mentioned, fetch data from all 4 platforms.
    
    6. Focus on requirements and expand terms accordingly.
    
    #
    
    ### 📝 TARGET SCHEMAS (Use these exact field names)
    {json.dumps(simplified_schemas, indent=2)}
    
    #
    
    ### ✅ REQUIRED OUTPUT FORMAT
    Return valid JSON only.
    
    #
    
    {{
      "query_type": "SPJ",
      "thought_process": "User asked for 'Cyber Security'. Expanding to include: Cybersecurity, Ethical Hacking, InfoSec, Network Security.",
      "expanded_terms": ["Cyber Security", "Cybersecurity", "Ethical Hacking", "InfoSec", "Network Security"],
      "providers": {{
        "coursera": {{
          "$or": [
            {{ "Title": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }},
            {{ "Skills": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }}
          ]
        }},
        "udacity": {{
           "$or": [
            {{ "Title": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }},
            {{ "What you learn": {{ "$regex": "\\\\b(Cyber Security|Ethical Hacking|InfoSec|Network Security)\\\\b", "$options": "i" }} }}
          ]
        }}
        // ... Generate for Simplilearn and FutureLearn similarly
      }}
    }}
    """


    try:
        raw_text = call_gemini_with_retry(prompt)

        if not raw_text:
            logger.warning("Empty response from Gemini")
            return {"query_type": "SPJ", "providers": {}}

        parsed = _find_balanced_json(raw_text)

        if parsed is None:
            logger.warning("Could not parse JSON from LLM response")
            # Fallback: Return empty to avoid crash
            return {"query_type": "SPJ", "providers": {}}

        # Log the expansion to verify it worked
        if "expanded_terms" in parsed:
            logger.info(f"🧠 LLM Expanded Terms: {parsed['expanded_terms']}")

        return parsed

    except Exception as e:
        logger.error(f"Gemini query generation failed: {e}")
        return {"query_type": "SPJ", "providers": {}}
