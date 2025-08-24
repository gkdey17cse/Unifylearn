# --- CRITICAL: Mapping from Schema Field Names to Database Field Names ---
SCHEMA_TO_DB_FIELD_MAP = {
    "coursera": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Skills Covered": "Skills",
        "Main Category": "Category",
        "Sub-Category": "Sub-Category",
        "Average Rating": "Rating",
        "Estimated Duration": "Duration",
    },
    "futurelearn": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Main Category": "Category",
        "Estimated Duration": "Duration",
    },
    "simplilearn": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Main Category": "Category",
        "Skills Covered": "Skills",
    },
    "udacity": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Estimated Duration": "Duration",
        "Program Type": "Program Type",
    },
}


def translate_query_to_db_fields(query_obj, provider):
    """
    Recursively translates a query object from schema field names to real database field names.
    """
    translation_map = SCHEMA_TO_DB_FIELD_MAP.get(provider, {})
    translated_obj = {}

    for key, value in query_obj.items():
        if not key.startswith("$") and key in translation_map:
            new_key = translation_map[key]
        else:
            new_key = key

        if isinstance(value, dict):
            translated_obj[new_key] = translate_query_to_db_fields(value, provider)
        elif isinstance(value, list):
            translated_obj[new_key] = [
                (
                    translate_query_to_db_fields(item, provider)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]
        else:
            translated_obj[new_key] = value

    return translated_obj
