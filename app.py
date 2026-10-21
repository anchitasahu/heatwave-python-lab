"""Vercel WSGI entrypoint for the Climate Lab dashboard."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs

from climatelabweb.app import api_response


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "climatelabweb"


def application(
    environ: dict[str, object],
    start_response: Callable[[str, list[tuple[str, str]]], object],
) -> list[bytes]:
    path = str(environ.get("PATH_INFO", "/"))
    if path.startswith("/api/"):
        query_string = str(environ.get("QUERY_STRING", ""))
        payload, status = api_response(path, parse_qs(query_string))
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        content_type = "application/json; charset=utf-8"
    else:
        filename = "index.html" if path in {"/", "/index.html"} else path.lstrip("/")
        static_path = (WEB_DIR / filename).resolve()
        if filename not in {"index.html", "app.js", "styles.css"} or not static_path.is_file():
            status = 404
            body = b'{"error":"Static file not found."}'
            content_type = "application/json; charset=utf-8"
        else:
            status = 200
            body = static_path.read_bytes()
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
            }[static_path.suffix]

    status_line = f"{status} {HTTPStatus(status).phrase}"
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ]
    start_response(status_line, headers)
    return [body]
