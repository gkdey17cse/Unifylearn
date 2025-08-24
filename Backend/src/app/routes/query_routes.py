# src/app/routes/query_routes.py
from flask import Blueprint, jsonify, request
from src.app.nlp.parser_rule_based import parse_user_query
from src.app.nlp.llm_interface import (
    analyze_query_with_llm,
    generate_mongo_queries_with_llm,
)
from src.app.services.federation_service import run_federated_query
from src.app.services.plan_builder import PROVIDERS

bp = Blueprint("query", __name__, url_prefix="")


@bp.route("/query", methods=["POST"])
def query_endpoint():
    """
    Accepts a POST request with 'query' field and:
    - Parses query using rule-based parser (fallback / lightweight)
    - Optionally asks LLM to produce executable MongoDB plans using schema
    - Runs federated query (using LLM plans if valid, otherwise rule-based plans)
    """
    body = request.get_json(silent=True) or {}
    q = body.get("query") or body.get("q") or ""
    if not q:
        return jsonify({"error": "Please provide JSON body with 'query' field"}), 400

    # 1) Lightweight rule-based parsing (fast, deterministic fallback)
    parsed = parse_user_query(q)

    # 2) LLM context (free-text analysis; useful for logging / UI)
    llm_context = analyze_query_with_llm(q)

    # 3) Generate actual Mongo-executable plans with LLM (schema-aware)
    #    PROVIDERS contains db/coll/fields that we pass as schema
    try:
        llm_plans = generate_mongo_queries_with_llm(q, PROVIDERS)
    except Exception as e:
        llm_plans = None
        # don't raise — fallback happens in federation layer

    # 4) Execute federated query — prefer llm_plans if valid; fallback to rule-based
    result = run_federated_query(parsed, llm_plans=llm_plans)

    return jsonify(
        {
            "query": q,
            "parsed_query": parsed,
            "llm_context": llm_context,
            "llm_plans": llm_plans,  # helpful for debugging in the response
            "took_seconds": result["meta"]["took_seconds"],
            "out_file": result["meta"]["out_file"],
            "errors": result["meta"]["errors"],
            "results_count": len(result["results"]),
            "results_preview": result["results"][:10],
        }
    )
