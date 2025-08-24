# src/app/query_handler.py
import os , json
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_executor.provider_executor import execute_provider_query
from src.app.response_formatter import unifyResponse
from src.app.results.saver import save_results


def processUserQuery(userQuery):
    # STEP 1: Generate intelligent queries using enhanced LLM
    generated_queries = generate_queries(userQuery)
    print(
        "\n--- LLM Queries (Schema Fields) ---\n",
        json.dumps(generated_queries, indent=2),
    )

    all_results = []
    debug_info = {
        "user_query": userQuery,
        "llm_generated_queries": generated_queries,
        "execution_results": {},
    }

    # STEP 2: Execute queries for each provider
    for provider, schema_field_query in generated_queries.items():
        print(f"\n--- Processing {provider} ---")

        sanitized_docs, result_info = execute_provider_query(
            provider, schema_field_query, userQuery
        )
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

    # STEP 3: Save results
    output_dir = os.getenv("OUTPUT_DIR", "./results")
    out_path = save_results(userQuery, debug_info, all_results, output_dir)

    print(f"\n--- Process Complete. Results saved to {out_path} ---")
    return {"query": userQuery, "results": all_results, "debug": debug_info}
