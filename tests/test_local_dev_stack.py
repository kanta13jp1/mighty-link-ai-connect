import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_local_dev_stack as verifier


def write_valid_project(root: Path) -> None:
    (root / "firebase.json").write_text(
        json.dumps(
            {
                "hosting": {"site": "mighty-link-ai-connect-13d22", "public": "."},
                "emulators": {
                    "auth": {"port": 9099},
                    "functions": {"port": 5001},
                    "hosting": {"port": 5000},
                    "ui": {"enabled": True, "port": 4000},
                    "singleProjectMode": True,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / ".firebaserc").write_text(
        json.dumps({"projects": {"default": "mighty-link-ai-connect-13d22"}}, indent=2),
        encoding="utf-8",
    )
    supabase = root / "supabase"
    migrations = supabase / "migrations"
    migrations.mkdir(parents=True)
    (supabase / "config.toml").write_text(
        """
project_id = "mighty-link-ai-connect-local"

[api]
enabled = true
port = 54321

[db]
port = 54322

[db.seed]
enabled = true
sql_paths = ["./seed.sql"]

[studio]
enabled = true
port = 54323

[auth]
enabled = true
site_url = "http://localhost:3000"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (supabase / "seed.sql").write_text(
        "insert into public.profiles (user_id, name, email) values ('u1', 'Local User', 'u1@example.test');\n",
        encoding="utf-8",
    )
    (migrations / "20260615000000_test.sql").write_text("select 1;\n", encoding="utf-8")


def check_by_key(report: dict, key: str) -> dict:
    return next(check for check in report["checks"] if check["key"] == key)


def test_valid_local_stack_static_config_passes(tmp_path):
    write_valid_project(tmp_path)

    report = verifier.build_report(tmp_path)

    assert report["status"] == "ok"
    assert check_by_key(report, "firebase.emulators.auth")["state"] == "ok"
    assert check_by_key(report, "supabase.db.port")["state"] == "ok"
    assert check_by_key(report, "supabase.seed.synthetic")["state"] == "ok"


def test_missing_firebase_emulator_is_critical(tmp_path):
    write_valid_project(tmp_path)
    firebase_json = json.loads((tmp_path / "firebase.json").read_text(encoding="utf-8"))
    del firebase_json["emulators"]["auth"]
    (tmp_path / "firebase.json").write_text(json.dumps(firebase_json), encoding="utf-8")

    report = verifier.build_report(tmp_path)

    assert report["status"] == "critical"
    assert check_by_key(report, "firebase.emulators.auth")["state"] == "critical"


def test_seed_company_email_is_critical(tmp_path):
    write_valid_project(tmp_path)
    (tmp_path / "supabase" / "seed.sql").write_text(
        "insert into public.profiles (email) values ('person@ml-mightylink.com');\n",
        encoding="utf-8",
    )

    report = verifier.build_report(tmp_path)

    assert report["status"] == "critical"
    assert check_by_key(report, "supabase.seed.synthetic")["state"] == "critical"


def test_current_env_rejects_non_local_supabase_db_url_without_leaking_password(tmp_path):
    write_valid_project(tmp_path)
    env = {
        "SUPABASE_DB_URL": "postgresql://postgres:super-secret@db.example.supabase.co:5432/postgres"
    }

    report = verifier.build_report(tmp_path, env=env, check_env=True)

    check = check_by_key(report, "local_env.supabase_db_url")
    assert report["status"] == "critical"
    assert check["state"] == "critical"
    assert check["details"]["hostname"] == "db.example.supabase.co"
    assert "super-secret" not in json.dumps(check, ensure_ascii=False)


def test_current_env_accepts_local_supabase_db_url(tmp_path):
    write_valid_project(tmp_path)
    env = {"SUPABASE_DB_URL": "postgresql://postgres:postgres@127.0.0.1:54322/postgres"}

    report = verifier.build_report(tmp_path, env=env, check_env=True)

    assert report["status"] == "ok"
    assert check_by_key(report, "local_env.supabase_db_url")["state"] == "ok"
