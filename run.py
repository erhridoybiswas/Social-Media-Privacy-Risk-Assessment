"""Convenience launcher: python run.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="127.0.0.1", port=port, debug=debug)