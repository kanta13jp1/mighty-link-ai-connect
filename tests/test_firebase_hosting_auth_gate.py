#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Regression guards for the Firebase Hosting authentication boundary."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIREBASE_CONFIG = PROJECT_ROOT / "firebase.json"


def load_hosting_config() -> dict:
    return json.loads(FIREBASE_CONFIG.read_text(encoding="utf-8"))["hosting"]


ALLOWED_STATIC_ASSETS = {"favicon.ico"}


def test_hosting_does_not_publish_application_files_directly():
    hosting = load_hosting_config()
    public_dir = PROJECT_ROOT / hosting["public"]

    assert hosting["public"] != "."
    assert public_dir.is_dir()
    assert not (public_dir / "index.html").exists()
    published_files = [
        path.name for path in public_dir.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    ]
    assert all(name in ALLOWED_STATIC_ASSETS for name in published_files)


def test_hosting_routes_every_non_static_request_to_authenticated_api():
    rewrites = load_hosting_config()["rewrites"]

    assert rewrites[-1] == {
        "source": "**",
        "run": {"serviceId": "api", "region": "us-central1"},
    }
