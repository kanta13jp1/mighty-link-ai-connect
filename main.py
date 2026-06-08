# -*- coding: utf-8 -*-
"""
Mighty Skill-Bridge: Firebase Cloud Functions Python Entrypoint
Author: Antigravity 2.0 (AI Agent)

This module serves as the entrypoint for Firebase Cloud Functions (Python).
It wraps the FastAPI application from `src.app` using `a2wsgi` to make it compatible
with the WSGI execution context expected by the Firebase functions runner.
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app
from src.app import app
from a2wsgi import ASGIMiddleware

# Initialize Firebase Admin SDK
try:
    initialize_app()
except ValueError:
    # Already initialized (e.g. during local tests)
    pass

# Convert FastAPI (ASGI) application to WSGI
wsgi_app = ASGIMiddleware(app)

# Export the "api" function mapped in firebase.json
@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Bridges incoming Firebase functions request to FastAPI ASGI app."""
    status_str = "200 OK"
    headers_list = []

    def start_response(status, headers, exc_info=None):
        nonlocal status_str, headers_list
        status_str = status
        headers_list = headers
        return lambda body_data: None

    # Execute WSGI application using the request environment dict
    body_iter = wsgi_app(req.environ, start_response)
    body = b"".join(body_iter)
    if hasattr(body_iter, "close"):
        body_iter.close()

    # Extract status code integer
    try:
        status_code = int(status_str.split()[0])
    except (ValueError, IndexError):
        status_code = 200

    # Return decorated Response object compatible with Cloud Functions
    return https_fn.Response(
        response=body,
        status=status_code,
        headers=headers_list
    )
