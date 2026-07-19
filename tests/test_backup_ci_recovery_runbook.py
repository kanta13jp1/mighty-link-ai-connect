"""T870_1 test spec (written test-first): backup-CI recovery runbook.

R116 (HIGH, open): the Supabase Daily Backup CI has never succeeded since
6/22 — the WIF binding sits on the OLD project (100664750415 /
mighty-link-ai-connect-d7fa2) with the WRONG role (roles/iam.serviceAccountUser
instead of roles/iam.workloadIdentityUser), the private GCS bucket does not
exist, and the secrets are unregistered. T849_2 showed R116 alone blocks four
GA gates (PUBLIC-02/13/14/15), making it the largest single GA blocker.

The recovery is cloud+secret work owned by 人間 + Codex, so the Claude lane's
contribution is to make that execution mechanical and verifiable. This suite
pins the recovery runbook against the workflow it recovers, so the two cannot
drift: every repository secret the backup workflow consumes must be documented
in the runbook, the exact past mis-configuration must be called out, and no
secret VALUE may ever be committed into the runbook.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = PROJECT_ROOT / "docs" / "SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md"
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "supabase-backup.yml"

# ${{ secrets.NAME }} references in the workflow.
_SECRET_RE = re.compile(r"secrets\.([A-Z0-9_]+)")


def _runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def workflow_secret_names() -> set[str]:
    """Repository secrets the backup workflow consumes (github.token excluded)."""
    names = set(_SECRET_RE.findall(WORKFLOW.read_text(encoding="utf-8")))
    return {n for n in names if n != "GITHUB_TOKEN"}


def test_runbook_exists():
    assert RUNBOOK.exists(), f"missing {RUNBOOK}"


def test_every_workflow_secret_is_documented():
    """Runbook/workflow drift guard: a secret added to the workflow without a
    registration step in the runbook would leave the operator unable to finish
    the recovery."""
    text = _runbook_text()
    undocumented = sorted(n for n in workflow_secret_names() if n not in text)
    assert not undocumented, f"secrets used by the workflow but not documented: {undocumented}"


def test_runbook_names_the_correct_wif_role_and_the_past_mistake():
    text = _runbook_text()
    assert "roles/iam.workloadIdentityUser" in text, "correct WIF role must be stated"
    assert "roles/iam.serviceAccountUser" in text, "the wrong role actually used must be called out"


def test_runbook_records_the_old_project_root_cause():
    text = _runbook_text()
    assert "100664750415" in text or "d7fa2" in text, "root-cause project must be identified"


def test_runbook_defines_verification_and_completion_criteria():
    text = _runbook_text()
    for cue in ("workflow_dispatch", "PUBLIC-02", "R116"):
        assert cue in text, f"runbook must reference {cue}"


def test_runbook_contains_no_secret_values():
    """The runbook documents secret NAMES and commands only — never values."""
    text = _runbook_text()
    forbidden = [
        r"postgres(?:ql)?://[^\s`<]*:[^\s`<]*@",      # a real DB URL with a password
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",         # SA key material
        r"\bAIza[0-9A-Za-z_\-]{20,}",                  # Google API key
        r"\bghp_[0-9A-Za-z]{20,}",                     # GitHub PAT
    ]
    hits = [p for p in forbidden if re.search(p, text)]
    assert not hits, f"runbook must not contain secret values (matched: {hits})"
