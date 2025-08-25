import google.generativeai as genai
import os
import json
import re
from typing import Dict, Any
from src.app.universal_schema import ESSENTIAL_FIELDS  # Import the essential fields

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def enrich_course_data(
    original_data: Dict[str, Any], universal_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use LLM to fill missing ESSENTIAL fields based on available data.
    """
    # Focus only on essential fields that are missing or empty
    essential_fields_to_enrich = []

    for field in ESSENTIAL_FIELDS:
        current_value = universal_data.get(field)
        is_empty = (
            current_value is None
            or current_value == ""
            or current_value == []
            or current_value == 0
            or (isinstance(current_value, list) and len(current_value) == 0)
        )

        if is_empty:
            essential_fields_to_enrich.append(field)

    if not essential_fields_to_enrich:
        return universal_data

    # Build prompt focused on essential fields only
    prompt = f"""
You are a data enrichment expert. Based on the available course information, fill in these ESSENTIAL missing fields: {essential_fields_to_enrich}

**COURSE INFORMATION:**
Title: {universal_data.get('title', 'Unknown')}
Description: {universal_data.get('description', 'No description')}
Provider: {universal_data.get('provider', 'Unknown')}

**ORIGINAL DATA (for context):**
{json.dumps(original_data, indent=2)}

**INSTRUCTIONS:**
1. Focus ONLY on these fields: {essential_fields_to_enrich}
2. For skills: Extract from description and context
3. For category: Infer from title and description  
4. For prerequisites: Suggest reasonable requirements based on level
5. For learning_outcomes: Extract key learning points from description within 30 to 40 words max
6. Be concise and accurate
7. For language: Default to "English" if not specified
8. For viewers: Provide a reasonable estimate if unknown

**OUTPUT FORMAT:** JSON with only the missing essential fields filled

**Example:** If missing "skills", "category", and "level":
{{
  "skills": ["Python", "Machine Learning", "Data Analysis"],
  "category": "Data Science",
  "level": "Intermediate"
}}

**Now fill these missing fields: {essential_fields_to_enrich}**
"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        # Extract JSON from response
        response_text = response.text.strip()
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if json_match:
            enriched_data = json.loads(json_match.group())
            # Merge the enriched data with existing universal data
            for key, value in enriched_data.items():
                if (
                    key in essential_fields_to_enrich
                ):  # FIXED: Use correct variable name
                    universal_data[key] = value

            return universal_data
        else:
            print("Could not extract JSON from LLM response")
            print(f"LLM Response: {response_text}")
            return universal_data

    except Exception as e:
        print(f"Error in LLM enrichment: {e}")
        return universal_data
