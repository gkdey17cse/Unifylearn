# main.py
import json
import os
from dotenv import load_dotenv
from src.app.query_generator.llm_query_builder import generate_queries
from src.app.query_generator.query_translator import translate_query_to_db_fields


def main():
    load_dotenv()

    print("Course Query Generator - Phase 1")
    print("=" * 50)

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
    print("-" * 40)

    generated_queries = generate_queries(user_query)

    if not generated_queries:
        print("No queries generated. Please try a different query.")
        return

    # Check if generated_queries is actually a dictionary
    if not isinstance(generated_queries, dict):
        print(f"ERROR: Expected dictionary but got {type(generated_queries)}")
        print(f"Content: {generated_queries}")
        return

    for provider, schema_query in generated_queries.items():
        print(f"\nProvider: {provider.upper()}")

        print("LLM Generated Query (Schema Fields):")
        print(json.dumps(schema_query, indent=2))

        try:
            db_query = translate_query_to_db_fields(schema_query, provider)

            print("\nTranslated Query (Database Fields):")
            print(json.dumps(db_query, indent=2))
        except Exception as e:
            print(f"Error translating query for {provider}: {e}")

        print("-" * 50)


if __name__ == "__main__":
    main()
