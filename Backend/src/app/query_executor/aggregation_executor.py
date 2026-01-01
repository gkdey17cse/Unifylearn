# src/app/query_executor/aggregation_executor.py
import json
from src.app.db_connection import dbMap, COLLECTION_MAP
from src.app.query_generator.query_translator import translate_query_to_db_fields
from src.app.utils.logger import logger


def execute_aggregation_pipeline(provider, pipeline, user_query):
    provider_lower = provider.lower()
    db = dbMap.get(provider_lower)

    if db is None:
        logger.error(f"Database not configured for: {provider_lower}")
        return None, {"error": "DB not configured"}

    collection_name = COLLECTION_MAP.get(provider_lower)
    coll = db.get_collection(collection_name)

    # Translate the pipeline stages
    translated_pipeline = []
    for stage in pipeline:
        translated_stage = translate_query_to_db_fields(stage, provider_lower)
        translated_pipeline.append(translated_stage)

    try:
        logger.database(f"Executing aggregation on {provider_lower}")
        cursor = coll.aggregate(translated_pipeline)
        matched_docs = list(cursor)

        logger.info(f"Found {len(matched_docs)} documents from {provider}")

        result_info = {
            "collection": collection_name,
            "pipeline": translated_pipeline,
            "match_count": len(matched_docs),
            "execution_error": None,
        }

        return matched_docs, result_info

    except Exception as e:
        error_msg = f"Aggregation failed for {provider}: {str(e)}"
        logger.error(error_msg)
        return None, {
            "collection": collection_name,
            "pipeline": translated_pipeline,
            "match_count": 0,
            "execution_error": error_msg,
        }


def execute_cross_platform_aggregation(generated_queries, user_query):
    all_results = []
    execution_results = {}

    logger.aggregation("Starting cross-platform aggregation")

    # Get aggregation parameters
    sort_field = generated_queries.get("sort_field", "Number of viewers")
    sort_order = generated_queries.get("sort_order", -1)
    global_limit = generated_queries.get("global_limit", 10)

    logger.aggregation(
        f"Sorting by: {sort_field}, Order: {sort_order}, Limit: {global_limit}"
    )

    # Get data from all providers
    for provider, query in generated_queries.get("providers", {}).items():
        provider_lower = provider.lower()
        db = dbMap.get(provider_lower)

        if db is None:
            logger.warning(f"Database not available for: {provider_lower}")
            continue

        collection_name = COLLECTION_MAP.get(provider_lower)
        coll = db.get_collection(collection_name)

        # For cross-platform, extract the actual find query
        from src.app.query_executor.provider_executor import _extract_find_query_from_schema
        
        # Extract the actual find query from the schema structure
        find_query = _extract_find_query_from_schema(query)
        
        # If no specific conditions, use empty query to get all documents
        if not find_query:
            find_query = {}
        
        # Translate and execute the find query
        translated_query = translate_query_to_db_fields(find_query, provider_lower)

        try:
            cursor = coll.find(translated_query)
            matched_docs = list(cursor)
            logger.info(f"Found {len(matched_docs)} documents from {provider}")

            # Add provider info to each document
            for doc in matched_docs:
                doc["_provider"] = provider
                doc["_collection"] = collection_name

            all_results.extend(matched_docs)

            execution_results[provider] = {
                "collection": collection_name,
                "query": translated_query,
                "match_count": len(matched_docs),
                "execution_error": None,
            }

        except Exception as e:
            error_msg = f"Query failed for {provider}: {str(e)}"
            logger.error(error_msg)
            execution_results[provider] = {
                "collection": collection_name,
                "query": translated_query,
                "match_count": 0,
                "execution_error": error_msg,
            }

    # Perform cross-platform aggregation
    logger.aggregation(f"Performing aggregation on {len(all_results)} total documents")

    def get_sort_value(doc):
        value = doc.get(sort_field, 0)
        if isinstance(value, str):
            try:
                return int(value.replace(",", ""))
            except (ValueError, AttributeError):
                return 0
        return value or 0

    try:
        # Sort the combined results
        sorted_results = sorted(
            all_results, key=get_sort_value, reverse=(sort_order == -1)
        )

        # Apply global limit
        final_results = sorted_results[:global_limit]

        logger.success(f"Aggregation completed: {len(final_results)} final results")

        return final_results, execution_results

    except Exception as e:
        error_msg = f"Cross-platform aggregation failed: {str(e)}"
        logger.error(error_msg)
        return [], execution_results