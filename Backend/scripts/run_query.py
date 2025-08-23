# scripts/run_query.py
"""
Quick CLI: python scripts/run_query.py "Show me top 5 courses in Data Science from Coursera"
"""
import sys
from app.nlp.parser_rule_based import parse_user_query
from app.services.federation_service import run_federated_query


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/run_query.py "<your natural language query>"')
        sys.exit(1)
    q = sys.argv[1]
    parsed = parse_user_query(q)
    res = run_federated_query(parsed)
    print("Took (s):", res["meta"]["took_seconds"])
    print("Results returned:", len(res["results"]))
    for i, r in enumerate(res["results"][:10], 1):
        print(
            f"{i}. [{r.get('platform')}] {r.get('title')[:80]} (rating: {r.get('rating')})"
        )


if __name__ == "__main__":
    main()
