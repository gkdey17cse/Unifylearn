from flask import request, jsonify
from src.app.query_handler import processUserQuery


def initRoutes(app):
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/query", methods=["POST"])
    def query():
        data = request.json
        if not data or "query" not in data:
            return jsonify({"error": "Query is required"}), 400

        userQuery = data["query"]
        result = processUserQuery(userQuery)
        return jsonify(result)
