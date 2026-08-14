from pathlib import Path


REPORT = Path("docs/SALES_EMAIL_DISAPPEARANCE_FORENSIC_REPORT_2026-08-14.md")


def test_forensic_report_records_all_three_incident_windows() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "2026-07-25 16:51～17:32 JST" in text
    assert "2026-08-10 16:56:08～17:35:35 JST" in text
    assert "2026-08-14 15:00:22～17:52:30 JST" in text
    assert "INBOX=1" in text
    assert "INBOX=0" in text
    assert "Trash=690" in text


def test_forensic_report_separates_capability_from_execution_evidence() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "技術的容疑経路" in text
    assert "実行・設定条件の証拠が不足" in text
    assert "人物への嫌疑ではなく" in text
    assert "GMO側アクセスログが不可欠" in text


def test_forensic_report_includes_shared_mailbox_ceo_questions() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "2026-07-08 接続情報の起点" in text
    assert "複数の営業担当" in text
    assert "社長へ確認する事項" in text
    assert "パスワードそのものは再送・再掲せず" in text
    assert "12. 共有アカウントの共通パスワード運用を廃止" in text


def test_forensic_report_does_not_embed_mailbox_or_secret_values() -> None:
    text = REPORT.read_text(encoding="utf-8")

    forbidden = (
        "@mighty-link.com",
        "IMAP_PASSWORD=",
        "POP3_PASSWORD=",
        "SUPABASE_DB_URL=",
    )
    assert not any(value in text for value in forbidden)
