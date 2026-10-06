"""
app.py
======
Flask application factory and page routes.

Run with:
    python backend/app.py
or:
    python run.py
"""

import os
import sys

# Allow `python backend/app.py` to resolve the `backend` package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from backend.config import FRONTEND_DIR  # noqa: E402
from backend.models.database import init_db, seed_recommendations  # noqa: E402
from backend.routes.api import api_bp  # noqa: E402

PAGES = {
    "/": "index.html",
    "/assessment": "assessment.html",
    "/dashboard": "dashboard.html",
    "/report": "report.html",
    "/checklist": "checklist.html",
}


def create_app():
    """Build and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path="/static",
    )

    # Security headers (defence in depth for a static + JSON app).
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        return response

    # Initialise storage and the static recommendation catalogue.
    init_db()
    seed_recommendations()

    app.register_blueprint(api_bp)

    # ---- Static pages ----------------------------------------------------
    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, PAGES["/"])

    @app.route("/assessment")
    def assessment_page():
        return send_from_directory(FRONTEND_DIR, PAGES["/assessment"])

    @app.route("/dashboard")
    def dashboard_page():
        return send_from_directory(FRONTEND_DIR, PAGES["/dashboard"])

    @app.route("/report")
    def report_page():
        return send_from_directory(FRONTEND_DIR, PAGES["/report"])

    @app.route("/checklist")
    def checklist_page():
        return send_from_directory(FRONTEND_DIR, PAGES["/checklist"])

    # ---- JSON error handling (never leak stack traces) -------------------
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({
            "error": error.name.lower().replace(" ", "_"),
            "message": error.description,
        }), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):  # pragma: no cover - safety net
        app.logger.exception("Unhandled application error")
        return jsonify({
            "error": "server_error",
            "message": "An unexpected error occurred. Please try again.",
        }), 500

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print("=" * 68)
    print(" Social Media Privacy Risk Assessment Framework")
    print(" Educational, defensive, synthetic-data-only privacy tool")
    print(f" Open:  http://127.0.0.1:{port}/")
    print("=" * 68)
    app.run(host="127.0.0.1", port=port, debug=debug)