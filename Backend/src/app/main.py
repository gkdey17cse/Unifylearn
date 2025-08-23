# src/app/main.py
from flask import Flask, jsonify
from app.routes.query_routes import bp as query_bp
from app.routes.health_routes import bp as health_bp


def create_app():
    app = Flask(__name__)

    # Register blueprints without a url_prefix so paths are /query and /health
    app.register_blueprint(query_bp)
    app.register_blueprint(health_bp)

    # Optional: a simple home route so hitting "/" in the browser doesn't 404
    @app.get("/")
    def home():
        return (
            jsonify(
                {
                    "message": "Federated NL Query API is running",
                    "try": {
                        "health": "/health (GET)",
                        "query": '/query (POST, JSON body: {"query": "..."})',
                    },
                }
            ),
            200,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
