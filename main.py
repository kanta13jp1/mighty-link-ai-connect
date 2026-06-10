# -*- coding: utf-8 -*-
"""
Mighty Skill-Bridge: Firebase Cloud Functions Python Entrypoint
Author: Antigravity 2.0 (AI Agent)

This module serves as the entrypoint for Firebase Cloud Functions (Python).
It wraps the FastAPI application from `src.app` using `a2wsgi` to make it compatible
with the WSGI execution context expected by the Firebase functions runner.
"""

import os
import threading
# Ensure critical environment variables exist to prevent gspread import crash in sandbox environments
if "APPDATA" not in os.environ:
    os.environ["APPDATA"] = os.environ.get("USERPROFILE") or os.environ.get("HOME") or os.path.expanduser("~")

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

# Convert FastAPI (ASGI) to WSGI lazily, on the first request.
# ASGIMiddleware starts a daemon thread running its asyncio event loop. The
# production runtime (functions-framework -> gunicorn) imports this module in
# the gunicorn master and then forks workers; threads do not survive fork, so
# a loop created at import time has no running thread inside the worker and
# every request blocks forever on run_coroutine_threadsafe(...).result().
_wsgi_app = None
_wsgi_lock = threading.Lock()


def _get_wsgi_app():
    global _wsgi_app
    if _wsgi_app is None:
        with _wsgi_lock:
            if _wsgi_app is None:
                _wsgi_app = ASGIMiddleware(app)
    return _wsgi_app

# Export the "api" function mapped in firebase.json
@https_fn.on_request(invoker="public")
def api(req: https_fn.Request) -> https_fn.Response:
    """Bridges incoming Firebase functions request to FastAPI ASGI app."""
    status_str = "200 OK"
    headers_list = []

    def start_response(status, headers, exc_info=None):
        nonlocal status_str, headers_list
        status_str = status
        headers_list = headers
        return lambda body_data: None

    # Copy and normalize WSGI environment to prevent routing drift in serverless environment
    environ = req.environ.copy()
    path_info = environ.get("PATH_INFO", "")
    script_name = environ.get("SCRIPT_NAME", "")
    
    # If SCRIPT_NAME is defined (e.g. /api or /admin) but PATH_INFO doesn't include it,
    # combine them to restore the full path for FastAPI's global routes.
    if script_name and not path_info.startswith(script_name):
        environ["PATH_INFO"] = script_name + path_info
        environ["SCRIPT_NAME"] = ""

    # Execute WSGI application using the normalized environment dict
    body_iter = _get_wsgi_app()(environ, start_response)
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
