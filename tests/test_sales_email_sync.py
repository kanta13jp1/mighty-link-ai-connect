# -*- coding: utf-8 -*-
import os
import sys
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

import app

app.BASIC_AUTH_USERNAME = "ml-admin-c10b9f"
app.BASIC_AUTH_PASSWORD = "e83yDi0WsxcASDXHLhvvezoW4uVBCQX_"

client = TestClient(app.app)

@patch("sync_sales_emails.sync_sales_emails_pipeline")
def test_sync_sales_emails_endpoint_success(mock_pipeline):
    mock_pipeline.return_value = {
        "status": "success",
        "new_emails_count": 3
    }
    
    # Authorize with basic credentials using auth parameter
    response = client.post(
        "/api/sales-email/sync",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD)
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "new_emails_count": 3
    }
    mock_pipeline.assert_called_once_with(max_messages=None)


@patch("sync_sales_emails.sync_sales_emails_pipeline")
def test_sync_sales_emails_endpoint_with_max_messages(mock_pipeline):
    mock_pipeline.return_value = {
        "status": "success",
        "new_emails_count": 1000
    }
    
    response = client.post(
        "/api/sales-email/sync?max_messages=1000",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD)
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "new_emails_count": 1000
    }
    mock_pipeline.assert_called_once_with(max_messages=1000)


def test_sync_sales_emails_endpoint_unauthorized():
    response = client.post("/api/sales-email/sync")
    assert response.status_code == 401
