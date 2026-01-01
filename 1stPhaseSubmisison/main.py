# main.py
import json
import os
from dotenv import load_dotenv
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_generator.query_translator import translate_query_to_db_fields


def main():
    load_dotenv()

    print("Advanced Course Query Generator - SPJ & Aggregate Queries")
    print("=" * 60)

    while True:
        user_query = input("\nEnter your query (or 'quit' to exit): ").strip()

        if user_query.lower() == "quit":
            print("Exiting...")
            break

        if not user_query:
            print("Please enter a valid query.")
            continue

        try:
            process_query(user_query)
        except Exception as e:
            print(f"Error: {str(e)}")


def process_query(user_query):
    print(f"\nProcessing query: '{user_query}'")
    print("-" * 50)

    generated_queries = generate_queries(user_query)

    if not generated_queries:
        print("No queries generated. Please try a different query.")
        return

    # Display query type and description
    query_type = generated_queries.get("query_type", "UNKNOWN")
    description = generated_queries.get("description", "No description")

    print(f"Query Type: {query_type}")
    print(f"Description: {description}")
    print("-" * 50)

    providers = generated_queries.get("providers", {})

    if not providers:
        print("No provider queries generated.")
        return

    for provider, schema_query in providers.items():
        print(f"\nProvider: {provider.upper()}")

        print("LLM Generated Query (Schema Fields):")
        print(json.dumps(schema_query, indent=2))

        try:
            # Translate schema fields to database fields
            db_query = translate_query_to_db_fields(schema_query, provider)

            print("\nTranslated Query (Database Fields):")
            print(json.dumps(db_query, indent=2))

            # Add query analysis
            analyze_query_structure(db_query, provider)

        except Exception as e:
            print(f"Error translating query for {provider}: {e}")

        print("-" * 50)


def analyze_query_structure(query, provider):
    """Analyze and display query structure for better understanding"""
    print(f"\nQuery Analysis for {provider.upper()}:")

    if isinstance(query, list):
        print("  Type: Aggregation Pipeline")
        for i, stage in enumerate(query):
            stage_type = list(stage.keys())[0] if stage else "unknown"
            print(f"  Stage {i+1}: {stage_type}")
    elif isinstance(query, dict):
        if any(key.startswith("$") for key in query.keys()):
            print("  Type: Complex Find Operation")
            for key in query.keys():
                print(f"  Operation: {key}")
        else:
            print("  Type: Simple Find Operation")
            print(f"  Fields: {list(query.keys())}")


if __name__ == "__main__":
    main()
