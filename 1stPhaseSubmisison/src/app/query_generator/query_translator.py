# src/app/query_generator/query_translator.py
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
        "Price": "Price",
    },
    "futurelearn": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Main Category": "Category",
        "Estimated Duration": "Duration",
        "Price": "Price",
    },
    "simplilearn": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Main Category": "Category",
        "Skills Covered": "Skills",
        "Price": "Price",
    },
    "udacity": {
        "Course Title": "Title",
        "Course URL": "URL",
        "Brief Description": "Short Intro",
        "Estimated Duration": "Duration",
        "Program Type": "Program Type",
        "Price": "Price",
    },
}


def translate_query_to_db_fields(query_obj, provider):
    """
    Recursively translates query objects from schema fields to database fields.
    Handles both find queries and aggregation pipelines.
    """
    # Handle aggregation pipelines (arrays)
    if isinstance(query_obj, list):
        return [translate_query_to_db_fields(stage, provider) for stage in query_obj]

    # Handle individual query objects (dict)
    translation_map = SCHEMA_TO_DB_FIELD_MAP.get(provider, {})
    translated_obj = {}

    for key, value in query_obj.items():
        # Translate field names (skip operators starting with $)
        if not key.startswith("$") and key in translation_map:
            new_key = translation_map[key]
        else:
            new_key = key

        # Recursively translate nested objects
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
