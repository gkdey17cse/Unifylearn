# src/app/routes.py
from flask import request, jsonify
from src.app.query_handler import generate_queries_only
from datetime import datetime


def register_routes(app):
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify(
            {
                "status": "healthy",
                "message": "Course Query Generator API is running",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.route("/query", methods=["POST"])
    def handle_query():
        try:
            data = request.get_json()
            if not data or "query" not in data:
                return (
                    jsonify({"success": False, "error": "Query parameter is required"}),
                    400,
                )

            user_query = data["query"].strip()
            if not user_query:
                return (
                    jsonify({"success": False, "error": "Query cannot be empty"}),
                    400,
                )

            queries = generate_queries_only(user_query)

            return jsonify(
                {
                    "success": True,
                    "query": user_query,
                    "generated_queries": queries,
                    "total_providers": len(queries),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Error generating queries: {str(e)}"}
                ),
                500,
            )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Endpoint not found",
                    "available_endpoints": ["GET /health", "POST /query"],
                }
            ),
            404,
        )
