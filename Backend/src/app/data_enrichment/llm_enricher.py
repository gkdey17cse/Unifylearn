# src/app/data_enrichment/llm_enricher.py
import google.generativeai as genai
import os
import json
import re
import time
import random
from typing import Dict, Any, List
from src.app.universal_schema import ESSENTIAL_FIELDS

# Track enrichment requests for rate limiting
last_enrichment_time = 0
enrichment_count = 0


def _enforce_enrichment_rate_limit():
    """Enforce rate limiting for enrichment calls"""
    global last_enrichment_time, enrichment_count
    current_time = time.time()

    # Reset counter if it's been more than 60 seconds
    if current_time - last_enrichment_time > 60:
        enrichment_count = 0
        last_enrichment_time = current_time

    # More reasonable limit - 15 per minute
    if enrichment_count >= 15:
        sleep_time = 60 - (current_time - last_enrichment_time)
        if sleep_time > 0:
            print(f"⏳ Enrichment rate limit: Waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        enrichment_count = 0
        last_enrichment_time = time.time()

    enrichment_count += 1
    time.sleep(0.5)  # Reduced delay


def safe_gemini_call(prompt, max_retries=2):
    """Safe wrapper for Gemini calls with retry logic"""
    for attempt in range(max_retries + 1):
        try:
            _enforce_enrichment_rate_limit()
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text if response.text else None
        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 + attempt
                print(f"🔄 Retrying enrichment in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"⚠️  LLM enrichment failed: {e}")
                return None
    return None


def _extract_json_from_response(response_text):
    """Extract JSON from LLM response with better error handling"""
    if not response_text:
        return None

    # Clean the response
    cleaned_text = re.sub(
        r"```(?:json)?", "", response_text, flags=re.IGNORECASE
    ).strip()

    # Try direct parsing first
    if cleaned_text.startswith("{") and cleaned_text.endswith("}"):
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

    # Try to find JSON object
    json_match = re.search(r'\{[^{}]*"[^"]*"[^{}]*\}', cleaned_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


def _clean_and_extract_skills(what_you_learn_text, description, title):
    """
    Intelligently extract skills from 'What you learn' content
    """
    if not what_you_learn_text:
        return []

    # Clean the text
    clean_text = re.sub(r"\s+", " ", what_you_learn_text).strip()

    # Common technical skills to look for
    technical_skills = [
        "python",
        "java",
        "javascript",
        "machine learning",
        "deep learning",
        "ai",
        "data analysis",
        "statistics",
        "linear algebra",
        "calculus",
        "probability",
        "neural networks",
        "natural language processing",
        "computer vision",
        "reinforcement learning",
        "supervised learning",
        "unsupervised learning",
        "data structures",
        "algorithms",
        "sql",
        "nosql",
        "database",
        "cloud computing",
        "aws",
        "azure",
        "google cloud",
        "docker",
        "kubernetes",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "tableau",
        "power bi",
    ]

    # Extract skills based on patterns
    skills_found = []

    # Look for technical terms
    for skill in technical_skills:
        if skill.lower() in clean_text.lower():
            skills_found.append(skill.title())

    # Remove duplicates and return
    return list(set(skills_found))[:10]  # Limit to 10 most relevant skills


def _create_learning_outcomes(what_you_learn_text, description, title):
    """
    Create meaningful learning outcomes from course content
    """
    if not what_you_learn_text:
        return []

    # Clean and split the text
    clean_text = re.sub(r"\s+", " ", what_you_learn_text).strip()

    # Split by major topics (looking for capitalized phrases or common patterns)
    topics = re.findall(r"[A-Z][a-zA-Z\s]{5,}(?=\s*[A-Z]|$)", clean_text)

    # Create learning outcomes
    outcomes = []
    for topic in topics[:8]:  # Limit to 8 main topics
        topic_clean = topic.strip()
        if len(topic_clean) > 10 and len(topic_clean) < 100:
            outcome = f"Understand and apply {topic_clean.lower()}"
            outcomes.append(outcome)

    # If no good topics found, create generic outcomes based on course title
    if not outcomes:
        if "machine learning" in title.lower():
            outcomes = [
                "Understand fundamental machine learning concepts",
                "Apply ML algorithms to real-world problems",
                "Evaluate model performance and metrics",
                "Preprocess and analyze data for ML",
            ]
        elif "artificial intelligence" in title.lower():
            outcomes = [
                "Understand AI principles and techniques",
                "Implement AI algorithms and systems",
                "Solve problems using AI approaches",
                "Evaluate AI system performance",
            ]
        elif "data" in title.lower():
            outcomes = [
                "Analyze and interpret complex datasets",
                "Apply statistical methods to data analysis",
                "Create data visualizations and reports",
                "Use data to drive decision-making",
            ]
        else:
            outcomes = [
                "Master core concepts presented in the course",
                "Apply learned techniques to practical scenarios",
                "Develop critical thinking in the subject area",
                "Build projects demonstrating course knowledge",
            ]

    return outcomes[:6]  # Limit to 6 outcomes


def enrich_course_data(
    original_data: Dict[str, Any], universal_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use LLM to intelligently enrich course data with high-quality formatting
    """
    # Skip enrichment if we're hitting rate limits
    if enrichment_count >= 15:  # More conservative limit
        print("⚠️  Skipping enrichment due to rate limits")
        return universal_data

    # Check which fields actually need enrichment
    fields_need_enrichment = []
    for field in ["skills", "learning_outcomes", "category", "level"]:
        current_value = universal_data.get(field)
        is_empty = (
            current_value is None
            or current_value == ""
            or current_value == []
            or (isinstance(current_value, list) and len(current_value) == 0)
        )
        if is_empty:
            fields_need_enrichment.append(field)

    if not fields_need_enrichment:
        print("ℹ️  No essential fields need enrichment")
        return universal_data

    print(f"🔧 Attempting intelligent enrichment for: {fields_need_enrichment}")

    # Get source data for context
    title = universal_data.get("title", "")
    description = universal_data.get("description", "")
    what_you_learn = original_data.get("What you learn", "")
    prerequisites = original_data.get("Prequisites", "")
    provider = universal_data.get("provider", "")

    # Build a comprehensive prompt for high-quality enrichment
    prompt = f"""
You are an expert course data analyst. Your task is to enrich the course information with high-quality, structured data.

**COURSE INFORMATION:**
- Title: {title}
- Description: {description}
- Provider: {provider}
- What You Learn Content: {what_you_learn[:1000]}  # Truncate to avoid token limits
- Prerequisites: {prerequisites[:500]}

**TASK:**
Enrich the following fields with HIGH-QUALITY, MEANINGFUL content:

{fields_need_enrichment}

**SPECIFIC INSTRUCTIONS FOR EACH FIELD:**

1. **SKILLS:**
   - Extract 5-8 most relevant technical/professional skills
   - Focus on concrete, measurable skills (not vague concepts)
   - Format as a clean list: ["Python", "Machine Learning", "Data Analysis"]
   - Remove duplicates and overly generic terms

2. **LEARNING_OUTCOMES:**
   - Create 4-6 clear, actionable learning objectives
   - Start with action verbs: "Understand", "Apply", "Analyze", "Create", "Evaluate"
   - Make them specific and measurable
   - Format as a clean list

3. **CATEGORY:**
   - Assign to one primary category from: Data Science, Computer Science, Business, 
     Technology, Engineering, Mathematics, Statistics, Artificial Intelligence, 
     Machine Learning, Web Development, Cloud Computing, Cybersecurity
   - Be specific but not too narrow

4. **LEVEL:**
   - Assign appropriate level: Beginner, Intermediate, Advanced
   - Consider prerequisites and course content complexity

**OUTPUT FORMAT:**
Return ONLY a JSON object with the enriched fields. Example:
{{
  "skills": ["Python", "Data Analysis", "Statistical Modeling"],
  "learning_outcomes": [
    "Understand fundamental statistical concepts",
    "Apply Python for data analysis tasks",
    "Create data visualizations using matplotlib"
  ],
  "category": "Data Science",
  "level": "Intermediate"
}}

**Now enrich these fields: {fields_need_enrichment}**
"""

    try:
        print("🤖 Calling Gemini for intelligent enrichment...")
        response_text = safe_gemini_call(prompt)

        if not response_text:
            print("⚠️  No response from LLM enrichment")
            return _apply_fallback_enrichment(
                universal_data, original_data, fields_need_enrichment
            )

        # Extract JSON from response
        enriched_data = _extract_json_from_response(response_text)

        if enriched_data:
            # Apply the enriched data
            enriched_fields = []
            for field, value in enriched_data.items():
                if field in fields_need_enrichment:
                    universal_data[field] = value
                    enriched_fields.append(field)

            print(
                f"✅ Successfully enriched {len(enriched_fields)} fields: {enriched_fields}"
            )
            return universal_data
        else:
            print("⚠️  Could not parse JSON from LLM response, using fallback")
            return _apply_fallback_enrichment(
                universal_data, original_data, fields_need_enrichment
            )

    except Exception as e:
        print(f"❌ Error in LLM enrichment: {e}")
        return _apply_fallback_enrichment(
            universal_data, original_data, fields_need_enrichment
        )


def _apply_fallback_enrichment(
    universal_data: Dict[str, Any],
    original_data: Dict[str, Any],
    fields_needed: List[str],
) -> Dict[str, Any]:
    """
    Apply intelligent fallback enrichment when LLM fails
    """
    print("🔄 Applying intelligent fallback enrichment...")

    title = universal_data.get("title", "").lower()
    description = universal_data.get("description", "")
    what_you_learn = original_data.get("What you learn", "")

    for field in fields_needed:
        if field == "skills" and not universal_data.get("skills"):
            universal_data["skills"] = _clean_and_extract_skills(
                what_you_learn, description, title
            )

        elif field == "learning_outcomes" and not universal_data.get(
            "learning_outcomes"
        ):
            universal_data["learning_outcomes"] = _create_learning_outcomes(
                what_you_learn, description, title
            )

        elif field == "category" and not universal_data.get("category"):
            # Infer category from title and description
            if any(
                term in title
                for term in ["machine learning", "ml", "ai", "artificial intelligence"]
            ):
                universal_data["category"] = "Artificial Intelligence"
            elif any(
                term in title for term in ["data science", "data analysis", "analytics"]
            ):
                universal_data["category"] = "Data Science"
            elif any(
                term in title for term in ["web", "frontend", "backend", "full stack"]
            ):
                universal_data["category"] = "Web Development"
            elif any(term in title for term in ["cloud", "aws", "azure", "gcp"]):
                universal_data["category"] = "Cloud Computing"
            else:
                universal_data["category"] = "Technology"

        elif field == "level" and not universal_data.get("level"):
            # Infer level from prerequisites and content
            prereq = original_data.get("Prequisites", "").lower()
            if any(term in prereq for term in ["advanced", "expert", "experienced"]):
                universal_data["level"] = "Advanced"
            elif any(
                term in prereq
                for term in ["intermediate", "basic knowledge", "familiar"]
            ):
                universal_data["level"] = "Intermediate"
            else:
                universal_data["level"] = "Beginner"

    print("✅ Fallback enrichment applied")
    return universal_data