# src/app/query_handler.py
import os
import json
from datetime import datetime
from bson import json_util
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_executor.provider_executor import execute_provider_query
from src.app.query_executor.aggregation_executor import (
    execute_aggregation_pipeline,
    execute_cross_platform_aggregation,
)
from src.app.response_formatter import unifyResponse
from src.app.results.saver import save_results
from src.app.utils.logger import logger


def save_enriched_courses(all_results, output_dir):
    enriched_courses = []

    for result in all_results:
        enriched_course = {
            **result["unified_data"],
            "original_provider_id": result["original_data"].get("_id"),
            "source_provider": result["provider"],
        }
        enriched_courses.append(enriched_course)

    os.makedirs(output_dir, exist_ok=True)
    enriched_path = os.path.join(output_dir, "polished_results.json")

    with open(enriched_path, "w", encoding="utf-8") as fh:
        json.dump(enriched_courses, fh, default=json_util.default, ensure_ascii=False, indent=2)

    return enriched_path


def save_generated_queries(generated_queries, user_query, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    queries_path = os.path.join(output_dir, "generated_queries.json")

    queries_data = {
        "user_query": user_query,
        "generated_queries": generated_queries,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(queries_path, "w", encoding="utf-8") as fh:
        json.dump(queries_data, fh, default=json_util.default, ensure_ascii=False, indent=2)

    return queries_path


def save_raw_execution_results(execution_results, user_query, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    raw_results_path = os.path.join(output_dir, "raw_execution_results.json")

    raw_results_data = {
        "user_query": user_query,
        "execution_results": execution_results,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(raw_results_path, "w", encoding="utf-8") as fh:
        json.dump(raw_results_data, fh, default=json_util.default, ensure_ascii=False, indent=2)

    return raw_results_path


def save_raw_documents(raw_documents_by_provider, user_query, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    raw_docs_path = os.path.join(output_dir, "raw_documents.json")

    raw_docs_data = {
        "user_query": user_query,
        "raw_documents": raw_documents_by_provider,
        "total_raw_documents": sum(
            len(docs) for docs in raw_documents_by_provider.values()
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(raw_docs_path, "w", encoding="utf-8") as fh:
        json.dump(raw_docs_data, fh, default=json_util.default, ensure_ascii=False, indent=2)

    return raw_docs_path


def process_aggregation_query(generated_queries, user_query):
    all_results = []
    execution_results = {}
    raw_documents_by_provider = {}

    query_type = generated_queries.get("query_type", "SPJ")
    aggregation_strategy = generated_queries.get(
        "aggregation_strategy", "provider_level"
    )

    logger.aggregation(
        f"Processing {query_type} query with {aggregation_strategy} strategy"
    )

    if aggregation_strategy == "cross_platform":
        logger.aggregation("Executing cross-platform aggregation")
        combined_results, provider_results = execute_cross_platform_aggregation(
            generated_queries, user_query
        )

        execution_results.update(provider_results)

        # Process the combined results
        for doc in combined_results:
            provider = doc.get("_provider", "unknown")
            unified_data = unifyResponse(provider, doc)

            all_results.append(
                {
                    "provider": provider,
                    "original_data": doc,
                    "unified_data": unified_data,
                    "enrichment_applied": True,
                }
            )

            if provider not in raw_documents_by_provider:
                raw_documents_by_provider[provider] = []
            raw_documents_by_provider[provider].append(doc)

    else:
        logger.aggregation("Executing provider-level aggregation")
        for provider, query in generated_queries.get("providers", {}).items():
            logger.info(f"Processing {provider}")

            # Check if this is an aggregation pipeline (list) or find query (dict)
            if isinstance(query, list):
                sanitized_docs, result_info = execute_aggregation_pipeline(
                    provider, query, user_query
                )
            else:
                sanitized_docs, result_info = execute_provider_query(
                    provider, query, user_query
                )

            execution_results[provider] = result_info
            raw_documents_by_provider[provider] = sanitized_docs or []

            if sanitized_docs:
                logger.info(f"Found {len(sanitized_docs)} documents for {provider}")
                for doc in sanitized_docs:
                    unified_data = unifyResponse(provider.lower(), doc)

                    all_results.append(
                        {
                            "provider": provider.lower(),
                            "original_data": doc,
                            "unified_data": unified_data,
                            "enrichment_applied": True,
                        }
                    )

    return all_results, execution_results, raw_documents_by_provider


def processUserQuery(userQuery):
    try:
        # STEP 1: Generate queries
        generated_queries = generate_queries(userQuery)
        logger.info(f"Query type: {generated_queries.get('query_type', 'SPJ')}")

        all_results = []
        execution_results = {}
        raw_documents_by_provider = {}

        query_type = generated_queries.get("query_type", "SPJ")
        debug_info = {
            "user_query": userQuery,
            "llm_generated_queries": generated_queries,
            "query_type": query_type,
            "execution_results": execution_results,
        }

        # STEP 2: Execute queries based on type
        if query_type == "AGGREGATE":
            all_results, execution_results, raw_documents_by_provider = (
                process_aggregation_query(generated_queries, userQuery)
            )
        else:
            # SPJ query processing
            logger.info("Processing as SPJ query")
            for provider, schema_field_query in generated_queries.get(
                "providers", {}
            ).items():
                logger.info(f"Processing {provider}")

                sanitized_docs, result_info = execute_provider_query(
                    provider, schema_field_query, userQuery
                )
                execution_results[provider] = result_info
                debug_info["execution_results"][provider] = result_info
                raw_documents_by_provider[provider] = sanitized_docs or []

                if sanitized_docs:
                    logger.info(f"Found {len(sanitized_docs)} documents for {provider}")
                    for doc in sanitized_docs:
                        unified_data = unifyResponse(provider.lower(), doc)

                        all_results.append(
                            {
                                "provider": provider.lower(),
                                "original_data": doc,
                                "unified_data": unified_data,
                                "enrichment_applied": True,
                            }
                        )

        # STEP 3: Save results
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        output_dir = os.getenv("OUTPUT_DIR", "./results")
        query_output_dir = os.path.join(output_dir, ts)

        queries_path = save_generated_queries(
            generated_queries, userQuery, query_output_dir
        )
        raw_results_path = save_raw_execution_results(
            execution_results, userQuery, query_output_dir
        )
        raw_docs_path = save_raw_documents(
            raw_documents_by_provider, userQuery, query_output_dir
        )
        polished_path = save_enriched_courses(all_results, query_output_dir)
        debug_path = save_results(userQuery, debug_info, all_results, query_output_dir)

        logger.success(f"All files saved to {query_output_dir}")
        logger.info(f"Total results: {len(all_results)}")

        # Prepare clean results for frontend
        frontend_results = []
        for result in all_results:
            frontend_results.append(
                {
                    **result["unified_data"],
                    "source_provider": result["provider"],
                    "original_provider_id": result["original_data"].get("_id"),
                    "enrichment_applied": result.get("enrichment_applied", False),
                }
            )

        return {
            "query": userQuery,
            "results": frontend_results,
            "total_results": len(frontend_results),
            "debug": debug_info,
            "output_directory": query_output_dir,
        }

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"query": userQuery, "results": [], "total_results": 0, "error": str(e)}