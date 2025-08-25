# src/app/data_enrichment/uniform_formatter.py
from typing import Dict, Any, List
import re
from src.app.data_enrichment.llm_enricher import enrich_course_data
from src.app.universal_schema import FIELD_MAPPING, ESSENTIAL_FIELDS


def format_to_universal_schema(
    original_data: Dict[str, Any], provider: str
) -> Dict[str, Any]:
    """
    Convert provider-specific data to universal schema format with focus on essential fields.
    """
    # Initialize only with essential fields
    universal_data = {
        "title": "",
        "url": "",
        "description": "",
        "category": "",
        "language": "",
        "skills": [],
        "instructors": [],
        "duration": "",
        "site": "",
        "level": "",
        "viewers": 0,
        "prerequisites": [],
        "learning_outcomes": [],
        "price": "",
        "provider": provider.capitalize(),  # Keep provider for context
    }

    # Map only essential fields from original data
    for universal_field in ESSENTIAL_FIELDS:
        if universal_field not in FIELD_MAPPING:
            continue

        source_fields = FIELD_MAPPING[universal_field]
        for source_field in source_fields:
            if source_field in original_data and original_data[source_field] not in [
                None,
                "null",
                "NaN",
                "",
                "None",
            ]:
                value = original_data[source_field]

                # Skip if value is essentially empty
                if isinstance(value, str) and value.strip() == "":
                    continue

                # Apply field-specific transformations
                if universal_field == "skills" and isinstance(value, str):
                    # Convert comma-separated skills to list, filter out empty/numeric-only
                    skills_list = [
                        skill.strip() for skill in value.split(",") if skill.strip()
                    ]
                    universal_data[universal_field] = [
                        skill for skill in skills_list if not skill.isdigit()
                    ]

                elif universal_field == "instructors" and isinstance(value, str):
                    # Convert comma-separated instructors to list
                    universal_data[universal_field] = [
                        instructor.strip()
                        for instructor in value.split(",")
                        if instructor.strip()
                    ]

                elif universal_field == "viewers" and isinstance(value, str):
                    # Convert formatted numbers like "7,667" to integer
                    clean_value = value.replace(",", "").replace(" ", "")
                    numeric_match = re.search(r"(\d+)", clean_value)
                    if numeric_match:
                        universal_data[universal_field] = int(numeric_match.group(1))

                elif universal_field in [
                    "prerequisites",
                    "learning_outcomes",
                ] and isinstance(value, str):
                    # Convert long text to list of bullet points
                    # Split by sentences or newlines for better processing
                    sentences = re.split(r"[.!?\n]", value)
                    universal_data[universal_field] = [
                        s.strip()
                        for s in sentences
                        if s.strip() and len(s.strip()) > 10
                    ]

                else:
                    universal_data[universal_field] = value
                break

    # Use LLM to fill in missing ESSENTIAL information
    try:
        enriched_data = enrich_course_data(original_data, universal_data)
        return enriched_data
    except Exception as e:
        print(
            f"LLM enrichment failed for {universal_data.get('title', 'unknown')}: {e}"
        )
        # Return the formatted data even if LLM fails
        return universal_data


def ensure_essential_fields(final_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all essential fields have proper values for frontend.
    LLM should have filled these, but we ensure consistency.
    """
    # Ensure arrays are never null and have meaningful content
    for array_field in ["skills", "instructors", "prerequisites", "learning_outcomes"]:
        if final_data.get(array_field) is None:
            final_data[array_field] = []
        elif isinstance(final_data[array_field], list) and not final_data[array_field]:
            # If empty array, provide default based on field type
            if array_field == "skills" and final_data.get("description"):
                # Extract skills from description as fallback
                description = final_data["description"].lower()
                potential_skills = [
                    "python",
                    "tensorflow",
                    "pytorch",
                    "machine learning",
                    "deep learning",
                    "ai",
                    "data science",
                    "java",
                    "javascript",
                ]
                final_data[array_field] = [
                    skill for skill in potential_skills if skill in description
                ]

    # Ensure strings have meaningful defaults
    for string_field in [
        "title",
        "url",
        "description",
        "category",
        "language",
        "duration",
        "site",
        "level",
        "price",
    ]:
        if not final_data.get(string_field) or final_data[string_field] in [
            "",
            "null",
            "None",
        ]:
            if string_field == "language" and not final_data.get(string_field):
                final_data[string_field] = "English"  # Default assumption
            elif string_field == "site" and not final_data.get(string_field):
                final_data[string_field] = final_data.get("provider", "Online")
            else:
                final_data[string_field] = ""

    # Ensure numbers have sensible defaults
    if final_data.get("viewers") is None or final_data["viewers"] == 0:
        # Set reasonable default based on course type
        final_data["viewers"] = 1000  # Reasonable default

    # Clean up skills array (remove any numeric-only entries)
    if isinstance(final_data.get("skills"), list):
        final_data["skills"] = [
            skill
            for skill in final_data["skills"]
            if skill and not (isinstance(skill, str) and skill.isdigit())
        ]

    return final_data
