# src/app/query_handler.py
import json
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_generator.query_translator import translate_query_to_db_fields


def generate_queries_only(userQuery):
    """
    Phase 1: Generate and display queries without execution
    """
    try:
        print("PHASE 1: QUERY GENERATION")
        print(f"User Query: '{userQuery}'")

        generated_queries = generate_queries(userQuery)
        final_queries = {}

        for provider, schema_query in generated_queries.items():
            print(f"\n{provider.upper()} Query:")
            print("Schema-based query (from LLM):")
            print(json.dumps(schema_query, indent=2))

            db_query = translate_query_to_db_fields(schema_query, provider)
            final_queries[provider] = db_query

            print("Translated to DB fields:")
            print(json.dumps(db_query, indent=2))
            print("-" * 40)

        print(f"Generated queries for {len(final_queries)} providers")

        return final_queries

    except Exception as e:
        print(f"Error generating queries: {str(e)}")
        raise e
