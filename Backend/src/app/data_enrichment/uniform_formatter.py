# src/app/data_enrichment/uniform_formatter.py - UPDATED VERSION
from typing import Dict, Any
import re
from src.app.data_enrichment.llm_enricher import enrich_course_data
from src.app.universal_schema import FIELD_MAPPING, ESSENTIAL_FIELDS
from src.app.utils.logger import logger


def _clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text)
    cleaned = re.sub(r"[^\w\s.,!?;:-]", "", cleaned)
    return cleaned.strip()


def format_to_universal_schema(
    original_data: Dict[str, Any], provider: str
) -> Dict[str, Any]:
    """
    Convert provider-specific data to universal schema format
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
    }

    # NEW: Preserve relevance scores if they exist in original data
    if "relevance_probability" in original_data:
        universal_data["relevance_probability"] = original_data["relevance_probability"]
    if "relevance_score" in original_data:
        universal_data["relevance_score"] = original_data["relevance_score"]

    # ... (rest of the existing function remains the same) ...

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

    # Use LLM for intelligent enrichment
    try:
        enriched_data = enrich_course_data(original_data, universal_data)
        if enriched_data != universal_data:
            enriched_data["_enrichment_applied"] = True
        return _ensure_high_quality_output(enriched_data)

    except Exception as e:
        logger.warning(f"LLM enrichment failed: {e}")
        return _ensure_high_quality_output(universal_data)


def _ensure_high_quality_output(final_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all output is high-quality and properly formatted
    """
    # ... (existing function remains the same, it will preserve relevance scores) ...

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
