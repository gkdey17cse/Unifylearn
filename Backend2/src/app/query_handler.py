# src/app/query_handler.py
import os
import json
from datetime import datetime
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_executor.provider_executor import execute_provider_query
from src.app.response_formatter import unifyResponse
from src.app.results.saver import save_results


def save_enriched_courses(all_results, output_dir):
    """
    Save enriched courses in universal format to a separate file.
    """
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
        json.dump(enriched_courses, fh, ensure_ascii=False, indent=2)

    return enriched_path


def save_generated_queries(generated_queries, user_query, output_dir):
    """
    Save LLM generated queries to a separate file.
    """
    os.makedirs(output_dir, exist_ok=True)
    queries_path = os.path.join(output_dir, "generated_queries.json")

    queries_data = {
        "user_query": user_query,
        "generated_queries": generated_queries,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(queries_path, "w", encoding="utf-8") as fh:
        json.dump(queries_data, fh, ensure_ascii=False, indent=2)

    return queries_path


def save_raw_execution_results(execution_results, user_query, output_dir):
    """
    Save raw execution results from database queries.
    """
    os.makedirs(output_dir, exist_ok=True)
    raw_results_path = os.path.join(output_dir, "raw_execution_results.json")

    raw_results_data = {
        "user_query": user_query,
        "execution_results": execution_results,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(raw_results_path, "w", encoding="utf-8") as fh:
        json.dump(raw_results_data, fh, ensure_ascii=False, indent=2)

    return raw_results_path


def processUserQuery(userQuery):
    # STEP 1: Generate intelligent queries using enhanced LLM
    generated_queries = generate_queries(userQuery)
    print(
        "\n--- LLM Queries (Schema Fields) ---\n",
        json.dumps(generated_queries, indent=2),
    )

    all_results = []
    execution_results = {}
    debug_info = {
        "user_query": userQuery,
        "llm_generated_queries": generated_queries,
        "execution_results": execution_results,
    }

    # STEP 2: Execute queries for each provider
    for provider, schema_field_query in generated_queries.items():
        print(f"\n--- Processing {provider} ---")

        sanitized_docs, result_info = execute_provider_query(
            provider, schema_field_query, userQuery
        )
        execution_results[provider] = result_info
        debug_info["execution_results"][provider] = result_info

        if sanitized_docs:
            for doc in sanitized_docs:
                all_results.append(
                    {
                        "provider": provider.lower(),
                        "original_data": doc,
                        "unified_data": unifyResponse(provider.lower(), doc),
                    }
                )

    # STEP 3: Create timestamp-based directory for this query
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output_dir = os.getenv("OUTPUT_DIR", "./results")
    query_output_dir = os.path.join(output_dir, ts)

    # Save the three separate files
    queries_path = save_generated_queries(
        generated_queries, userQuery, query_output_dir
    )
    raw_results_path = save_raw_execution_results(
        execution_results, userQuery, query_output_dir
    )
    enriched_path = save_enriched_courses(all_results, query_output_dir)

    # Also save the complete debug info (optional)
    debug_path = save_results(userQuery, debug_info, all_results, query_output_dir)

    print(f"\n--- Results saved to {query_output_dir} ---")
    print(f"   # Generated queries: {queries_path}")
    print(f"   # Raw execution results: {raw_results_path}")
    print(f"   # Polished results: {enriched_path}")
    print(f"   # Debug info: {debug_path}")

    return {
        "query": userQuery,
        "results": all_results,
        "debug": debug_info,
        "output_directory": query_output_dir,
    }
