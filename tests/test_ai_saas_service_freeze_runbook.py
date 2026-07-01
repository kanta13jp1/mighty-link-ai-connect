from pathlib import Path


RUNBOOK = Path("docs/AI_SAAS_SERVICE_FREEZE_RUNBOOK.md")


def read_runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def test_t848_runbook_covers_all_requested_services():
    content = read_runbook()
    expected_terms = [
        "Anthropic",
        "OpenAI",
        "Google",
        "Microsoft",
        "Meta",
        "Amazon",
        "Apple",
        "xAI",
        "Grok",
        "Kimi",
        "MiMo",
        "DeepSeek",
        "BytePlus",
        "GitHub",
        "Slack",
        "Notion",
        "Obsidian",
        "Unity",
        "Figma",
        "Canva",
        "Reddit",
        "InsForge",
        "FireCrawl",
        "Firecrawl",
        "Discord",
        "Stripe",
        "Supabase",
        "Firebase",
        "お名前.com",
    ]
    for term in expected_terms:
        assert term in content


def test_t848_runbook_freezes_runtime_and_non_adopted_boundaries():
    content = read_runbook()
    required_phrases = [
        "本番ランタイム採用",
        "非採用・保留",
        "GA前に新しい外部AIモデルやSaaSを本番導線へ追加しない",
        "勝手に個人アカウントのkeyへfallbackしない",
        "public_paid_launch",
        "No-Go",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_deepseek_deprecation_and_gemini_model_are_explicit():
    content = read_runbook()
    assert "gemini-3.5-flash" in content
    assert "GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md" in content
    assert "deepseek-chat" in content
    assert "deepseek-reasoner" in content
    assert "2026-07-24 15:59 UTC" in content
    assert "deepseek-v4-flash" in content
    assert "deepseek-v4-pro" in content


def test_t848_runbook_forbids_secret_recording():
    content = read_runbook()
    assert "secret、OAuth token、API key、service account JSON、DB URL、Webhook URL、FTP/WordPress認証情報" in content
    assert "GitHub、Sheets、Issue、docs、NotebookLM、Slack、Notionへ記録しない" in content
