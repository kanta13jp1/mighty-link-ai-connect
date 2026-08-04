#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Regression tests for /favicon.ico endpoint."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


def test_favicon_returns_200_and_icon_media_type():
    for path in ["/favicon.ico", "/api/favicon.ico"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "image/x-icon" in response.headers.get("content-type", "").lower()
        assert len(response.content) > 0

