from flask import Flask
from src.app.routes import initRoutes
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret")

initRoutes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
