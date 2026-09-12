"""Verify API test storage isolation without importing the application module."""

import ast
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_api_fixture_isolates_storage_before_init_and_restores_state(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "tests" / "test_api.py"
    # Execute the actual fixture definition only; importing test_api would also
    # import app and initialize provider SDKs before this isolation check runs.
    fixture_node = next(
        node for node in ast.parse(source.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and node.name == "setup_test_db"
    )
    fake_app = SimpleNamespace(
        IS_MANAGED_RUNTIME=True,
        DATABASE_URL="test-only-cached-db-url",
        USE_SUPABASE=True,
        SUPABASE_SDK_ACTIVE=True,
        DATA_DIR="original-data",
        AUDIT_DIR="original-audit",
        AUDIT_LOG_FILE="original-audit-log",
        EXTERNAL_API_USAGE_LOG_FILE="original-usage-log",
        AI_FORCE_MOCK=False,
        GEMINI_READY=True,
    )
    data_dir = tmp_path / "data"
    audit_dir = data_dir / "audit"
    initialized = []

    def inspect_initialization():
        assert fake_app.IS_MANAGED_RUNTIME is False
        assert fake_app.DATABASE_URL == ""
        assert fake_app.USE_SUPABASE is False
        assert fake_app.SUPABASE_SDK_ACTIVE is False
        assert "K_SERVICE" not in os.environ
        assert "SUPABASE_DB_URL" not in os.environ
        assert fake_app.DATA_DIR == str(data_dir)
        assert fake_app.DB_PATH == str(data_dir / "mighty.db")
        assert fake_app.AUDIT_DIR == str(audit_dir)
        assert fake_app.AUDIT_LOG_FILE == str(audit_dir / "ai_audit.jsonl")
        assert fake_app.EXTERNAL_API_USAGE_LOG_FILE == str(data_dir / "external_api_usage.jsonl")
        assert fake_app.AI_FORCE_MOCK is True
        assert fake_app.GEMINI_READY is False
        assert audit_dir.is_dir()
        initialized.append(True)

    fake_app.init_db = inspect_initialization
    original_state = vars(fake_app).copy()
    monkeypatch.setenv("K_SERVICE", "test-only-managed-runtime")
    monkeypatch.setenv("SUPABASE_DB_URL", "test-only-runtime-db-url")
    namespace = {"app": fake_app, "pytest": pytest}
    exec(compile(ast.Module(body=[fixture_node], type_ignores=[]), str(source), "exec"), namespace)

    with pytest.MonkeyPatch.context() as settings:
        namespace["setup_test_db"].__wrapped__(tmp_path, settings)
        assert initialized == [True]

    # Existing globals and runtime detection are restored, and a previously
    # absent DB_PATH must not leak into other test modules.
    assert vars(fake_app) == original_state
    assert not hasattr(fake_app, "DB_PATH")
    assert os.environ["K_SERVICE"] == "test-only-managed-runtime"
    assert os.environ["SUPABASE_DB_URL"] == "test-only-runtime-db-url"
