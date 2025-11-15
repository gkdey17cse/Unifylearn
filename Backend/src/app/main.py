# src/app/main.py
from flask import Flask
from flask_cors import CORS
from src.app.routes import register_routes
from src.app.db_connection import initialize_db


def create_app():
    app = Flask(__name__)

    # Enable CORS for frontend communication
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Initialize database connection
    initialize_db()

    # Register routes
    register_routes(app)

    return app


if __name__ == "__main__":
    print("Calling main")
    app = create_app()
    print("Starting Flask server on http://localhost:5003")
    app.run(debug=True, host="0.0.0.0", port=5003)