# src/app/routes/query_routes.py
from flask import Blueprint, jsonify, request
from app.nlp.parser_rule_based import parse_user_query
from app.services.federation_service import run_federated_query

bp = Blueprint("query", __name__, url_prefix="")


@bp.route("/query", methods=["POST"])
def query_endpoint():
    body = request.get_json(silent=True) or {}
    q = body.get("query") or body.get("q") or ""
    if not q:
        return jsonify({"error": "please provide JSON body with 'query' field"}), 400
    parsed = parse_user_query(q)
    result = run_federated_query(parsed)
    # return summary + small preview
    return jsonify(
        {
            "query": q,
            "took_seconds": result["meta"]["took_seconds"],
            "out_file": result["meta"]["out_file"],
            "errors": result["meta"]["errors"],
            "results_count": len(result["results"]),
            "results_preview": result["results"][:10],
        }
    )
