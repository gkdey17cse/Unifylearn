import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app.semantic.semantic_expander import semantic_expander
from src.app.semantic.course_fetcher import course_fetcher


def check_semantic_setup():
    print("🔍 Checking Semantic Setup...")

    # Test course fetching
    print("1. Testing course fetching...")
    courses = course_fetcher.fetch_all_courses(
        limit_per_provider=50
    )  # Small limit for testing
    print(f"   ✅ Fetched {len(courses)} total courses")

    # Show sample from each provider
    providers = {}
    for course in courses:
        provider = course["provider"]
        if provider not in providers:
            providers[provider] = course

    for provider, sample_course in providers.items():
        print(f"   📦 {provider}: {sample_course['title'][:50]}...")

    # Test semantic initialization
    print("2. Testing semantic initialization...")
    semantic_expander.initialize_with_real_data()

    print("3. Testing query expansion...")
    test_queries = [
        "AI courses",
        "web development",
        "data science",
        "python programming",
    ]

    for query in test_queries:
        result = semantic_expander.expand_query(query)
        print(f"   🔍 '{query}' → {result['expanded_terms']}")

    print("✅ Semantic setup check completed!")


if __name__ == "__main__":
    check_semantic_setup()
