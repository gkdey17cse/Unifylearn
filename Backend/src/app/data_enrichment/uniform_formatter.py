# src/app/data_enrichment/uniform_formatter.py - UPDATED VERSION
from typing import Dict, Any , List
import re
from src.app.data_enrichment.batch_enricher import batch_enricher
from src.app.data_enrichment.llm_enricher import enrich_course_data
from src.app.universal_schema import FIELD_MAPPING, ESSENTIAL_FIELDS
from src.app.utils.logger import logger

# Global batch collection
courses_for_batch_enrichment = []

def format_to_universal_schema(
    original_data: Dict[str, Any], provider: str
) -> Dict[str, Any]:
    """
    Convert provider-specific data to universal schema format
    Prepare for batch enrichment
    """
    # Initialize with basic fields
    universal_data = {
        "title": _clean_text(original_data.get("Title", "")),
        "url": original_data.get("URL", ""),
        "description": _clean_text(original_data.get("Short Intro", "")),
        "category": "",
        "language": "English",
        "skills": [],
        "instructors": [],
        "duration": original_data.get("Duration", ""),
        "site": provider.capitalize(),
        "level": "",
        "viewers": 1000,  # Default
        "prerequisites": [],
        "learning_outcomes": [],
        "price": (
            "Free"
            if "free" in str(original_data.get("Program Type", "")).lower()
            else "Paid"
        ),
        "provider": provider.capitalize(),
        "_enrichment_applied": False,
        "original_data": original_data,  # Store original for batch processing
    }

    # Preserve relevance scores if they exist in original data
    if "relevance_probability" in original_data:
        universal_data["relevance_probability"] = original_data["relevance_probability"]
    if "relevance_score" in original_data:
        universal_data["relevance_score"] = original_data["relevance_score"]

    # Basic field mapping
    if "Skills" in original_data and original_data["Skills"]:
        raw_skills = original_data["Skills"]
        if isinstance(raw_skills, str):
            skills_list = [
                skill.strip() for skill in raw_skills.split(",") if skill.strip()
            ]
            universal_data["skills"] = [
                s for s in skills_list if len(s) > 2 and not s.isdigit()
            ]

    if "Instructors" in original_data and original_data["Instructors"]:
        instructors_text = original_data["Instructors"]
        if isinstance(instructors_text, str):
            instructors_list = [
                inst.strip() for inst in instructors_text.split(",") if inst.strip()
            ]
            universal_data["instructors"] = instructors_list[:5]

    # Don't enrich here - just prepare for batch processing
    return _ensure_high_quality_output(universal_data)

def process_batch_enrichment(courses_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process batch enrichment for multiple courses"""
    if not courses_data:
        return courses_data
    
    # Filter courses that need enrichment
    courses_needing_enrichment = []
    for course in courses_data:
        needs_enrichment = (
            not course.get('skills') or 
            not course.get('learning_outcomes') or
            not course.get('category') or
            not course.get('level')
        )
        if needs_enrichment:
            courses_needing_enrichment.append(course)
    
    if not courses_needing_enrichment:
        logger.info("ℹ️  No courses need batch enrichment")
        return courses_data
    
    logger.info(f"🤖 Preparing batch enrichment for {len(courses_needing_enrichment)} courses")
    
    # Process in batches of 20 to avoid token limits
    batch_size = 20
    enriched_courses = []
    
    for i in range(0, len(courses_needing_enrichment), batch_size):
        batch = courses_needing_enrichment[i:i + batch_size]
        logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(courses_needing_enrichment)-1)//batch_size + 1}")
        
        try:
            enriched_batch = batch_enricher.enrich_courses_batch(batch)
            enriched_courses.extend(enriched_batch)
        except Exception as e:
            logger.error(f"❌ Batch enrichment failed: {e}")
            # Fallback to individual enrichment
            for course in batch:
                try:
                    enriched_course = enrich_course_data(
                        course.get('original_data', {}),
                        course
                    )
                    enriched_courses.append(enriched_course)
                except Exception as individual_error:
                    logger.error(f"❌ Individual enrichment also failed: {individual_error}")
                    enriched_courses.append(course)
    
    # Merge enriched courses back
    enriched_dict = {course.get('title'): course for course in enriched_courses}
    final_courses = []
    
    for course in courses_data:
        if course.get('title') in enriched_dict:
            final_courses.append(enriched_dict[course.get('title')])
        else:
            final_courses.append(course)
    
    return final_courses

def _clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text)
    cleaned = re.sub(r"[^\w\s.,!?;:-]", "", cleaned)
    return cleaned.strip()

def _ensure_high_quality_output(final_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all output is high-quality and properly formatted
    """
    # Ensure arrays are clean
    for array_field in ["skills", "instructors", "prerequisites", "learning_outcomes"]:
        if final_data.get(array_field) is None:
            final_data[array_field] = []
        elif isinstance(final_data[array_field], list):
            cleaned_list = [
                item for item in final_data[array_field] if item and str(item).strip()
            ]
            final_data[array_field] = list(set(cleaned_list))

    # Ensure skills are properly formatted
    if final_data.get("skills"):
        final_data["skills"] = [
            skill.strip().title()
            for skill in final_data["skills"]
            if len(skill.strip()) > 2
        ]
        final_data["skills"] = final_data["skills"][:8]

    # Ensure category is meaningful
    if not final_data.get("category"):
        title = final_data.get("title", "").lower()
        if any(term in title for term in ["machine learning", "ml", "ai"]):
            final_data["category"] = "Artificial Intelligence"
        elif any(term in title for term in ["data science", "data analysis"]):
            final_data["category"] = "Data Science"
        elif any(term in title for term in ["web", "frontend", "backend"]):
            final_data["category"] = "Web Development"
        else:
            final_data["category"] = "Technology"

    return final_data