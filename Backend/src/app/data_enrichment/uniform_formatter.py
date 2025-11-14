# src/app/data_enrichment/uniform_formatter.py
from typing import Dict, Any, List
import re
from src.app.data_enrichment.llm_enricher import enrich_course_data
from src.app.universal_schema import FIELD_MAPPING, ESSENTIAL_FIELDS


def _clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""

    # Remove extra whitespace, newlines, and special characters
    cleaned = re.sub(r"\s+", " ", text)
    cleaned = re.sub(r"[^\w\s.,!?;:-]", "", cleaned)
    return cleaned.strip()


def _parse_duration(duration_text: str) -> str:
    """Parse and clean duration text"""
    if not duration_text:
        return ""

    # Extract meaningful duration information
    if "month" in duration_text.lower():
        months = re.search(r"(\d+)\s*month", duration_text.lower())
        if months:
            return f"{months.group(1)} months"

    if "week" in duration_text.lower():
        weeks = re.search(r"(\d+)\s*week", duration_text.lower())
        if weeks:
            return f"{weeks.group(1)} weeks"

    if "hour" in duration_text.lower():
        hours = re.search(r"(\d+)\s*hour", duration_text.lower())
        if hours:
            return f"{hours.group(1)} hours"

    return _clean_text(duration_text)


def _parse_viewers(viewers_text: str) -> int:
    """Parse viewers count from text"""
    if not viewers_text:
        return 1000  # Reasonable default

    # Extract numbers from text like "42,571" or "1,000 viewers"
    numbers = re.findall(r"[\d,]+", viewers_text)
    if numbers:
        try:
            return int(numbers[0].replace(",", ""))
        except ValueError:
            pass

    return 1000


def format_to_universal_schema(
    original_data: Dict[str, Any], provider: str
) -> Dict[str, Any]:
    """
    Convert provider-specific data to universal schema format with intelligent cleaning
    """
    print(
        f"🔄 Starting intelligent formatting for: {original_data.get('Title', 'Unknown')}"
    )

    # Initialize with cleaned, structured data
    universal_data = {
        "title": _clean_text(original_data.get("Title", "")),
        "url": original_data.get("URL", ""),
        "description": _clean_text(original_data.get("Short Intro", "")),
        "category": "",
        "language": "English",  # Default assumption
        "skills": [],
        "instructors": [],
        "duration": _parse_duration(original_data.get("Duration", "")),
        "site": provider.capitalize(),
        "level": "",
        "viewers": _parse_viewers(original_data.get("Number of viewers", "")),
        "prerequisites": [],
        "learning_outcomes": [],
        "price": (
            "Free"
            if "free" in str(original_data.get("Program Type", "")).lower()
            else "Paid"
        ),
        "provider": provider.capitalize(),
        "_enrichment_applied": False,
        "_original_fields_mapped": [],
    }

    # Map specific fields with intelligent cleaning
    mapped_fields = []

    # Handle skills specially - don't just copy, we'll use LLM for this
    if "Skills" in original_data and original_data["Skills"]:
        raw_skills = original_data["Skills"]
        if isinstance(raw_skills, str):
            # Basic cleaning but LLM will do proper extraction
            skills_list = [
                skill.strip() for skill in raw_skills.split(",") if skill.strip()
            ]
            universal_data["skills"] = [
                s for s in skills_list if len(s) > 2 and not s.isdigit()
            ]
            mapped_fields.append("Skills→skills")

    # Handle instructors
    if "Instructors" in original_data and original_data["Instructors"]:
        instructors_text = original_data["Instructors"]
        if isinstance(instructors_text, str):
            instructors_list = [
                inst.strip() for inst in instructors_text.split(",") if inst.strip()
            ]
            universal_data["instructors"] = instructors_list[
                :5
            ]  # Limit to 5 instructors
            mapped_fields.append("Instructors→instructors")

    # Handle prerequisites
    if "Prequisites" in original_data and original_data["Prequisites"]:
        prereq_text = original_data["Prequisites"]
        if isinstance(prereq_text, str):
            # Split into meaningful points
            sentences = re.split(r"[.!?\n]", prereq_text)
            prerequisites = [
                s.strip()
                for s in sentences
                if len(s.strip()) > 20 and len(s.strip()) < 150
            ]
            universal_data["prerequisites"] = prerequisites[
                :8
            ]  # Limit to 8 prerequisites
            mapped_fields.append("Prequisites→prerequisites")

    # Track mapped fields
    universal_data["_original_fields_mapped"] = mapped_fields
    print(f"📊 Initially mapped {len(mapped_fields)} fields from original data")

    # Use LLM for intelligent enrichment of complex fields
    try:
        print("🤖 Starting intelligent LLM enrichment...")
        enriched_data = enrich_course_data(original_data, universal_data)

        # Check if enrichment actually happened
        if enriched_data != universal_data:
            enriched_data["_enrichment_applied"] = True
            print("✅ LLM enrichment completed successfully")
        else:
            print("ℹ️  LLM enrichment skipped or no changes made")

        return _ensure_high_quality_output(enriched_data)

    except Exception as e:
        print(f"❌ LLM enrichment failed: {e}")
        # Return the formatted data even if LLM fails
        return _ensure_high_quality_output(universal_data)


def _ensure_high_quality_output(final_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all output is high-quality and properly formatted
    """
    print("🎨 Applying final quality enhancements...")

    # Ensure arrays are clean and meaningful
    for array_field in ["skills", "instructors", "prerequisites", "learning_outcomes"]:
        if final_data.get(array_field) is None:
            final_data[array_field] = []
        elif isinstance(final_data[array_field], list):
            # Remove empty strings and duplicates
            cleaned_list = [
                item for item in final_data[array_field] if item and str(item).strip()
            ]
            final_data[array_field] = list(set(cleaned_list))

    # Ensure skills are properly capitalized and clean
    if final_data.get("skills"):
        final_data["skills"] = [
            skill.strip().title()
            for skill in final_data["skills"]
            if len(skill.strip()) > 2
        ]
        final_data["skills"] = final_data["skills"][:10]  # Limit to 10 skills

    # Ensure learning outcomes are properly formatted
    if final_data.get("learning_outcomes"):
        final_data["learning_outcomes"] = [
            outcome.strip()
            for outcome in final_data["learning_outcomes"]
            if outcome and len(outcome.strip()) > 10
        ][
            :6
        ]  # Limit to 6 outcomes

    # Ensure category is meaningful
    if not final_data.get("category") or final_data["category"] in ["", "null", "None"]:
        title = final_data.get("title", "").lower()
        if any(term in title for term in ["machine learning", "ml", "ai"]):
            final_data["category"] = "Artificial Intelligence"
        elif any(term in title for term in ["data science", "data analysis"]):
            final_data["category"] = "Data Science"
        elif any(term in title for term in ["web", "frontend", "backend"]):
            final_data["category"] = "Web Development"
        else:
            final_data["category"] = "Technology"

    # Ensure level is properly set
    if not final_data.get("level") or final_data["level"] in ["", "null", "None"]:
        final_data["level"] = "Intermediate"  # Reasonable default

    # Ensure description is clean
    if final_data.get("description"):
        final_data["description"] = _clean_text(final_data["description"])
        if len(final_data["description"]) > 300:
            final_data["description"] = final_data["description"][:297] + "..."

    print("✅ Final quality enhancements applied")
    return final_data
