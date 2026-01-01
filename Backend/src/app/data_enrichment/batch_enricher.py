# src/app/data_enrichment/batch_enricher.py - NEW FILE
import google.generativeai as genai
import os
import json
import re
import time
from typing import Dict, List, Any
from src.app.utils.logger import logger


class BatchEnricher:
    def __init__(self):
        self.last_enrichment_time = 0

    def _enforce_rate_limit(self):
        """Enforce rate limiting for batch calls"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_enrichment_time

        if time_since_last_call < 5.0:  # 5 second minimum between batch calls
            sleep_time = 5.0 - time_since_last_call
            logger.info(
                f"⏳ Batch enrichment rate limit: Waiting {sleep_time:.1f} seconds..."
            )
            time.sleep(sleep_time)

        self.last_enrichment_time = time.time()

    def safe_batch_gemini_call(self, prompt, max_retries=2):
        """Safe wrapper for batch Gemini calls"""
        for attempt in range(max_retries + 1):
            try:
                self._enforce_rate_limit()
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                return response.text if response.text else None
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 3 + attempt
                    logger.info(
                        f"🔄 Retrying batch enrichment in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"⚠️  Batch LLM enrichment failed: {e}")
                    return None
        return None

    def create_batch_enrichment_prompt(self, courses_data: List[Dict[str, Any]]) -> str:
        """Create a comprehensive prompt for batch enrichment"""

        courses_info = []
        for i, course_data in enumerate(courses_data):
            title = course_data.get("title", "Unknown Title")
            description = course_data.get("description", "")
            what_you_learn = course_data.get("original_data", {}).get(
                "What you learn", ""
            )
            prerequisites = course_data.get("original_data", {}).get("Prequisites", "")
            provider = course_data.get("provider", "Unknown")

            courses_info.append(
                f"""
COURSE {i+1}:
- Title: {title}
- Provider: {provider}
- Description: {description[:300]}
- What You Learn: {what_you_learn[:500]}
- Prerequisites: {prerequisites[:200]}
"""
            )

        courses_text = "\n".join(courses_info)

        prompt = f"""
You are an expert course data analyst. Your task is to enrich multiple course records with high-quality, structured data in a single batch.

**COURSES TO ENRICH:**
{courses_text}

**TASK:**
For EACH course above, enrich the following fields:

1. **SKILLS:** Extract 5-8 most relevant technical/professional skills as a JSON list
2. **LEARNING_OUTCOMES:** Create 4-6 clear, actionable learning objectives as a JSON list
3. **CATEGORY:** Assign one primary category from: Data Science, Computer Science, Business, Technology, Engineering, Mathematics, Statistics, Artificial Intelligence, Machine Learning, Web Development, Cloud Computing, Cybersecurity, Programming, Software Development
4. **LEVEL:** Assign appropriate level: Beginner, Intermediate, Advanced

**CRITICAL REQUIREMENTS:**
- Return ONLY valid JSON, no other text
- Skills must be concrete and measurable (avoid vague terms)
- Learning outcomes must start with action verbs
- Category must be specific but not too narrow
- Level should match course content and prerequisites

**OUTPUT FORMAT:**
Return a JSON array where each element corresponds to the courses in order:

[
  {{
    "skills": ["Python", "Data Analysis", "Statistical Modeling"],
    "learning_outcomes": [
      "Understand fundamental statistical concepts",
      "Apply Python for data analysis tasks"
    ],
    "category": "Data Science",
    "level": "Intermediate"
  }},
  {{
    "skills": ["JavaScript", "React", "Frontend Development"],
    "learning_outcomes": [
      "Build interactive web applications with React",
      "Understand component-based architecture"
    ],
    "category": "Web Development", 
    "level": "Beginner"
  }}
  // ... more courses in same order as input
]

**Now enrich all {len(courses_data)} courses in batch:**
"""
        return prompt

    def extract_json_from_batch_response(
        self, response_text: str
    ) -> List[Dict[str, Any]]:
        """Extract JSON array from batch response"""
        if not response_text:
            return []

        # Clean the response
        cleaned_text = re.sub(
            r"```(?:json)?", "", response_text, flags=re.IGNORECASE
        ).strip()

        # Try to find JSON array
        json_match = re.search(r"\[.*\]", cleaned_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse batch JSON: {e}")

        return []

    def enrich_courses_batch(
        self, courses_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich multiple courses in a single batch call"""
        if not courses_data:
            return courses_data

        logger.info(f"🤖 Starting batch enrichment for {len(courses_data)} courses...")

        # Create batch prompt
        prompt = self.create_batch_enrichment_prompt(courses_data)

        # Call Gemini
        response_text = self.safe_batch_gemini_call(prompt)

        if not response_text:
            logger.error("❌ No response from batch enrichment")
            return self._apply_batch_fallback(courses_data)

        # Parse response
        enriched_data_list = self.extract_json_from_batch_response(response_text)

        if len(enriched_data_list) != len(courses_data):
            logger.error(
                f"❌ Batch enrichment returned {len(enriched_data_list)} items, expected {len(courses_data)}"
            )
            return self._apply_batch_fallback(courses_data)

        # Apply enrichment to each course
        enriched_courses = []
        for i, (course_data, enrichment) in enumerate(
            zip(courses_data, enriched_data_list)
        ):
            enriched_course = course_data.copy()
            enriched_course.update(enrichment)
            enriched_course["_enrichment_applied"] = True
            enriched_course["_batch_enriched"] = True
            enriched_courses.append(enriched_course)

        logger.info(f"✅ Successfully batch enriched {len(enriched_courses)} courses")
        return enriched_courses

    def _apply_batch_fallback(
        self, courses_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply fallback enrichment when batch fails"""
        logger.info("🔄 Applying batch fallback enrichment...")

        from .llm_enricher import enrich_course_data

        enriched_courses = []
        for course_data in courses_data:
            try:
                # Use individual enrichment as fallback
                enriched_course = enrich_course_data(
                    course_data.get("original_data", {}), course_data
                )
                enriched_course["_enrichment_applied"] = True
                enriched_course["_batch_enriched"] = False
                enriched_courses.append(enriched_course)
            except Exception as e:
                logger.error(f"❌ Fallback enrichment failed for course: {e}")
                course_data["_enrichment_applied"] = False
                course_data["_batch_enriched"] = False
                enriched_courses.append(course_data)

        return enriched_courses


# Global instance
batch_enricher = BatchEnricher()
