# Backend/run.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app.main import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Course Search Backend on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
