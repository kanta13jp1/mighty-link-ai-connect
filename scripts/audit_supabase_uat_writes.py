"""Offline schema-contract guard for the live UAT write verifier (T845/T921)."""

from pathlib import Path

from verify_supabase_uat_writes import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Artifact declaration for the lane-preflight evidence check.
EVIDENCE_PATH = PROJECT_ROOT / "exports" / "supabase_uat_writes_audit.md"


if __name__ == "__main__":
    raise SystemExit(main())
