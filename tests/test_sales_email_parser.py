import os
import sys
import sqlite3
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from sales_email_parser import SalesEmailParser
import parse_sales_emails as runner
import manage_db_migrations as migrations

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_sales_email_parser_fallback_project():
    parser = SalesEmailParser(api_key="mock_disabled_key")
    # 【急募】Java / AWS 設計エンジニア募集
    subject = "\u3010\u6025\u52df\u3011Java / AWS \u8a2d\u8a08\u30a8\u30f3\u30b8\u30cb\u30a2\u52df\u96c6"
    # 案件名: Java基幹システム開発\n単価: 70万〜80万円\n勤務地: 渋谷（週3日リモート可）\n即日開始で長期の案件です。
    body = "\u6848\u4ef6\u540d: Java\u57fa\u5e79\u30b7\u30b9\u30c5\u30e0\u958b\u767a\n\u5358\u4fa1: 70\u301c80\u4e07\u5186\n\u52e4\u52d9\u5730: \u6e0b\u8c37\uff08\u90313\u65e5\u30ea\u30e2\u30fc\u30c8\u53ef\uff09\n\u5373\u65e5\u958b\u59cb\u3067\u9577\u671f\u306e\u6848\u4ef6\u3067\u3059\u3002"

    res = parser.parse(subject, body)
    assert res.category == "project"
    assert res.project is not None
    assert "JAVA" in res.project.required_skills
    assert "AWS" in res.project.required_skills
    assert res.project.rate_min == 70
    assert res.project.rate_max == 80
    assert res.project.location == "\u6e0b\u8c37"
    assert res.project.remote_type == "hybrid"
    assert res.project.start_date_text == "\u5373\u65e5"
    assert res.project.duration_text == "\u9577\u671f"

def test_sales_email_parser_fallback_talent():
    parser = SalesEmailParser(api_key="mock_disabled_key")
    # 【稼働可能】30代のPython/Dockerエンジニア提案
    subject = "\u3010\u7a3c\u50cd\u53ef\u80fd\u301130\u4ee3\u306ePython/Docker\u30a8\u30f3\u30b8\u30cb\u30a2\u63d0\u6848"
    # 弊社所属の技術者をご紹介します。\n得意スキル: Python, Docker, PostgreSQL\n希望単価: 75万\n希望勤務地: 常駐（新宿）\n即日稼働可能です。
    body = "\u5f0a\u793e\u6240\u5c5e\u306e\u6280\u8853\u8005\u3092\u3054\u7d39\u4ecb\u3057\u307e\u3059\u3002\n\u5f97\u610f\u30b9\u30ad\u30eb: Python, Docker, PostgreSQL\n\u5e0c\u671b\u5358\u4fa1: 75\u4e07\n\u5e0c\u671b\u52e4\u52d9\u5730: \u5e38\u99d4\uff08\u65b0\u5bbf\uff09\n\u5373\u65e5\u7a3c\u50cd\u53ef\u80fd\u3067\u3059\u3002"

    res = parser.parse(subject, body)
    assert res.category == "talent"
    assert res.talent is not None
    assert "PYTHON" in res.talent.skills
    assert "DOCKER" in res.talent.skills
    assert res.talent.desired_rate_max == 75
    assert res.talent.desired_location == "\u65b0\u5bbf"
    assert res.talent.remote_preference == "onsite"
    assert res.talent.availability_text == "\u5373\u65e5"

def test_parse_sales_emails_cli_integration(tmp_path, monkeypatch):
    db_path = tmp_path / "test_mighty.db"
    
    # 1. Apply schema migration to test DB
    assert migrations.main(["apply", "--engine", "sqlite", "--sqlite-path", str(db_path)]) == 0

    # 2. Ingest test message
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sales_mailbox_sources(source_key, display_name, source_type)
            VALUES ('test_source', 'Test Source', 'manual_upload')
            """
        )
        source_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO sales_email_messages(
                mailbox_source_id, dedupe_key, sender_hash, normalized_subject,
                body_hash, body_excerpt, source_type, ingest_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                "a" * 64,
                "b" * 64,
                "\u3010\u6848\u4ef6\u7d39\u4ecb\u3011Oracle/SQL Server\u8a2d\u8a08\u6848\u4ef6",
                "c" * 64,
                "\u6e0b\u8c37\u3067\u306e\u30c7\u30fc\u30bf\u30d9\u30fc\u30b9\u8a2d\u8a08\u696d\u52d9\u3067\u3059\u3002\u5358\u4fa1\u306f60\u301c70\u4e07\u5186\u3001\u5373\u65e5\u958b\u59cb\u3002\u5e38\u99d4\u3067\u3059\u3002",
                "manual_upload",
                "new"
            )
        )
        conn.commit()

    # 3. Patch environment/credentials to enforce local SQLite fallback mode
    monkeypatch.setenv("USE_SUPABASE", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    # Run the batch parser against the temporary DB
    # We subclass/patch the DBAdapter in runner temporarily by patching DBAdapter constructor
    # or passing db_path
    original_init = runner.DBAdapter.__init__
    def test_init(self, path):
        self.use_supabase = False
        self.db_path = db_path
        self.sb_client = None
        self.sqlite_conn = sqlite3.connect(db_path)
        self.sqlite_conn.row_factory = sqlite3.Row

    monkeypatch.setattr(runner.DBAdapter, "__init__", test_init)

    # Execute main parse function
    exit_code = runner.main()
    assert exit_code == 0

    # 4. Verify results
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verify message status updated
        msg = cursor.execute("SELECT * FROM sales_email_messages WHERE id = 1").fetchone()
        assert msg["ingest_status"] == "parsed"

        # Verify project requirements table has a new record
        req = cursor.execute("SELECT * FROM project_requirements WHERE message_id = 1").fetchone()
        assert req is not None
        assert req["title"] == "【案件紹介】Oracle/SQL Server設計案件"
        assert req["rate_min"] == 60
        assert req["rate_max"] == 70
        assert req["location"] == "渋谷"
        assert req["remote_type"] == "onsite"

        # Verify skill tags were inserted
        tags = cursor.execute("SELECT * FROM requirement_skill_tags WHERE project_requirement_id = ?", (req["id"],)).fetchall()
        assert len(tags) > 0
        skill_names = [t["skill_name"] for t in tags]
        assert "ORACLE" in skill_names
        assert "SQL" in skill_names

        # Verify parse run log was written
        run = cursor.execute("SELECT * FROM email_parse_runs WHERE id = 1").fetchone()
        assert run is not None
        assert run["status"] == "succeeded"
        assert run["input_count"] == 1
        assert run["unique_count"] == 1
        assert run["parsed_entity_count"] == 1
