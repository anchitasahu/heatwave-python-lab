"""Vercel Flask entrypoint for the Climate Lab dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file

from climatelabweb.app import api_response, LOG


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "climatelabweb"
app = Flask(__name__)


@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def handle_request(path: str) -> Response | tuple[Response, int]:
    if request.path.startswith("/api/"):
        payload, status = api_response(request.path, request.args.to_dict(flat=False))
        return Response(
            json.dumps(payload, ensure_ascii=False, allow_nan=False),
            status=status,
            content_type="application/json; charset=utf-8",
            headers={"Cache-Control": "no-store"},
        )

    filename = "index.html" if path in {"", "index.html"} else path
    if filename not in {"index.html", "app.js", "styles.css"}:
        return jsonify({"error": "Static file not found."}), 404
    static_path = WEB_DIR / filename
    if not static_path.is_file():
        LOG.error("Static file is missing: %s", static_path)
        return jsonify({"error": "Static file not found."}), 404
    return send_file(static_path, max_age=0)
