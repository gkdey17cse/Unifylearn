# Backend/run.py
import sys
import os
from dotenv import load_dotenv  # <-- ADDED: Import load_dotenv

# Load environment variables from .env file
# This MUST be the first thing the application does to ensure all keys are loaded.
load_dotenv()                   # <-- ADDED: Call load_dotenv()

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app.main import create_app

app = create_app()

if __name__ == "__main__":
    print("🚀 Starting Course Search Backend on http://localhost:5000")
    print("📊 API endpoints available:")
    print("   POST /query - Process natural language queries")
    print("   GET  /health - Health check")
    print("   GET  /results - List all saved results")
    print("   GET  /results/<timestamp> - Get specific results")
    app.run(debug=True, host="0.0.0.0", port=5000)