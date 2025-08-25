# src/app/routes.py
from flask import request, jsonify, send_file
from src.app.query_handler import processUserQuery
import os
import json
from datetime import datetime


def register_routes(app):
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        return jsonify(
            {
                "status": "healthy",
                "message": "Course Search API Server is running",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.route("/query", methods=["POST"])
    def handle_query():
        """
        Main endpoint to process user queries
        Returns: JSON with course results and saves 4 files
        """
        try:
            data = request.get_json()
            if not data or "query" not in data:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Query parameter is required in JSON body",
                        }
                    ),
                    400,
                )

            user_query = data["query"].strip()
            if not user_query:
                return (
                    jsonify({"success": False, "error": "Query cannot be empty"}),
                    400,
                )

            # Process the query (this saves 4 JSON files)
            result = processUserQuery(user_query)

            # Return the enriched courses to frontend
            return jsonify(
                {
                    "success": True,
                    "query": user_query,
                    "results": result["results"],  # Clean course data for frontend
                    "total_results": len(result["results"]),
                    "output_directory": result["output_directory"],
                    "timestamp": result["output_directory"].split("/")[-1],
                    "saved_files": result.get("saved_files", {}),
                }
            )

        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Internal server error: {str(e)}"}
                ),
                500,
            )

    @app.route("/results", methods=["GET"])
    def list_all_results():
        """
        List all available result timestamps
        Returns: JSON with list of timestamp directories
        """
        try:
            output_dir = os.getenv("OUTPUT_DIR", "./results")
            if not os.path.exists(output_dir):
                return jsonify(
                    {
                        "success": True,
                        "available_results": [],
                        "message": "No results directory found",
                    }
                )

            timestamps = []
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    timestamps.append(item)

            return jsonify(
                {
                    "success": True,
                    "available_results": sorted(
                        timestamps, reverse=True
                    ),  # Newest first
                    "total_count": len(timestamps),
                }
            )
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Error listing results: {str(e)}"}
                ),
                500,
            )

    @app.route("/results/<timestamp>", methods=["GET"])
    def get_saved_results(timestamp):
        """
        Get polished results for a specific timestamp
        Returns: JSON with course data for frontend display
        """
        try:
            output_dir = os.getenv("OUTPUT_DIR", "./results")
            query_dir = os.path.join(output_dir, timestamp)

            # Load polished results (for frontend display)
            polished_path = os.path.join(query_dir, "polished_results.json")
            if os.path.exists(polished_path):
                with open(polished_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
                return jsonify(
                    {
                        "success": True,
                        "results": results,
                        "total_results": len(results),
                        "timestamp": timestamp,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Polished results not found for this timestamp",
                            "suggestion": "Check if the timestamp exists or try /results to list available timestamps",
                        }
                    ),
                    404,
                )

        except Exception as e:
            return (
                jsonify(
                    {"success": False, "error": f"Error loading results: {str(e)}"}
                ),
                500,
            )

    @app.route("/results/<timestamp>/files", methods=["GET"])
    def list_files_in_timestamp(timestamp):
        """
        List all 4 JSON files in a timestamp directory
        Returns: JSON with file information
        """
        try:
            output_dir = os.getenv("OUTPUT_DIR", "./results")
            query_dir = os.path.join(output_dir, timestamp)

            if not os.path.exists(query_dir):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Directory not found for timestamp {timestamp}",
                        }
                    ),
                    404,
                )

            files = []
            expected_files = [
                "generated_queries.json",
                "raw_execution_results.json",
                "polished_results.json",
                "debug_results.json",
            ]

            for file in os.listdir(query_dir):
                if file.endswith(".json"):
                    file_path = os.path.join(query_dir, file)
                    files.append(
                        {
                            "filename": file,
                            "size_bytes": os.path.getsize(file_path),
                            "size_human": f"{os.path.getsize(file_path) / 1024:.1f} KB",
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(file_path)
                            ).isoformat(),
                            "exists": True,
                        }
                    )

            # Check for missing expected files
            for expected_file in expected_files:
                if not any(f["filename"] == expected_file for f in files):
                    files.append(
                        {
                            "filename": expected_file,
                            "size_bytes": 0,
                            "size_human": "0 KB",
                            "modified": None,
                            "exists": False,
                        }
                    )

            return jsonify(
                {
                    "success": True,
                    "timestamp": timestamp,
                    "files": files,
                    "total_files": len([f for f in files if f["exists"]]),
                }
            )
        except Exception as e:
            return (
                jsonify({"success": False, "error": f"Error listing files: {str(e)}"}),
                500,
            )

    @app.route("/results/<timestamp>/<filename>", methods=["GET"])
    def get_saved_file(timestamp, filename):
        """
        Download a specific JSON file from a timestamp directory
        Returns: The actual JSON file content
        """
        try:
            output_dir = os.getenv("OUTPUT_DIR", "./results")
            query_dir = os.path.join(output_dir, timestamp)

            # Security check: prevent directory traversal
            if ".." in filename or "/" in filename or "\\" in filename:
                return jsonify({"success": False, "error": "Invalid filename"}), 400

            file_path = os.path.join(query_dir, filename)

            if not os.path.exists(file_path):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"File {filename} not found for timestamp {timestamp}",
                            "available_files": (
                                [
                                    f
                                    for f in os.listdir(query_dir)
                                    if f.endswith(".json")
                                ]
                                if os.path.exists(query_dir)
                                else []
                            ),
                        }
                    ),
                    404,
                )

            # Return the actual JSON file
            return send_file(
                file_path,
                mimetype="application/json",
                as_attachment=False,  # Display in browser instead of downloading
                download_name=filename,
            )

        except Exception as e:
            return (
                jsonify({"success": False, "error": f"Error loading file: {str(e)}"}),
                500,
            )

    @app.route("/api/query-example", methods=["GET"])
    def query_example():
        """
        Example endpoint showing how to use the /query endpoint
        Returns: Example usage instructions
        """
        return jsonify(
            {
                "message": "Example usage of /query endpoint",
                "example_request": {
                    "method": "POST",
                    "url": "/query",
                    "headers": {"Content-Type": "application/json"},
                    "body": {
                        "query": "Python courses from Coursera and Udemy for beginners"
                    },
                },
                "expected_response": {
                    "success": True,
                    "query": "Python courses from Coursera and Udemy for beginners",
                    "results": ["array of course objects"],
                    "total_results": 15,
                    "timestamp": "20240101T120000Z",
                    "output_directory": "./results/20240101T120000Z",
                },
            }
        )

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Endpoint not found",
                    "available_endpoints": [
                        "GET  /health",
                        "POST /query",
                        "GET  /results",
                        "GET  /results/<timestamp>",
                        "GET  /results/<timestamp>/files",
                        "GET  /results/<timestamp>/<filename>",
                        "GET  /api/query-example",
                    ],
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Internal server error",
                    "message": "Please check the server logs for details",
                }
            ),
            500,
        )
