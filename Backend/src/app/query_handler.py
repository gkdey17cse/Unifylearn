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
    Save enriched courses in universal format (polished_results.json)
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
    Save LLM generated queries (generated_queries.json)
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
    Save raw execution results (raw_execution_results.json)
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
    try:
        # STEP 1: Generate intelligent queries using enhanced LLM
        generated_queries = generate_queries(userQuery)
        print("\n--- LLM Queries ---\n", json.dumps(generated_queries, indent=2))

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
                    unified_data = unifyResponse(provider.lower(), doc)
                    all_results.append(
                        {
                            "provider": provider.lower(),
                            "original_data": doc,
                            "unified_data": unified_data,
                        }
                    )

        # STEP 3: Create timestamp-based directory and save ALL 4 files
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        output_dir = os.getenv("OUTPUT_DIR", "./results")
        query_output_dir = os.path.join(output_dir, ts)

        # Save all 4 JSON files
        queries_path = save_generated_queries(
            generated_queries, userQuery, query_output_dir
        )
        raw_results_path = save_raw_execution_results(
            execution_results, userQuery, query_output_dir
        )
        polished_path = save_enriched_courses(all_results, query_output_dir)
        debug_path = save_results(userQuery, debug_info, all_results, query_output_dir)

        print(f"\n--- All 4 JSON files saved to {query_output_dir} ---")
        print(f"   📋 Generated queries: {queries_path}")
        print(f"   🗄️  Raw execution results: {raw_results_path}")
        print(f"   ✨ Polished results: {polished_path}")
        print(f"   🐛 Debug info: {debug_path}")

        # Prepare clean results for frontend
        frontend_results = []
        for result in all_results:
            frontend_results.append(
                {
                    **result["unified_data"],
                    "source_provider": result["provider"],
                    "original_provider_id": result["original_data"].get("_id"),
                }
            )

        return {
            "query": userQuery,
            "results": frontend_results,
            "debug": debug_info,
            "output_directory": query_output_dir,
            "saved_files": {
                "generated_queries": queries_path,
                "raw_results": raw_results_path,
                "polished_results": polished_path,
                "debug_info": debug_path,
            },
        }

    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise e
