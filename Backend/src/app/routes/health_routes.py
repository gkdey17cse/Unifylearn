# src/app/routes/health_routes.py
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "Federated NL Query API"}), 200
