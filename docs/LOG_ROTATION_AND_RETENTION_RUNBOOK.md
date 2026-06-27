# ログローテーション・アクセスログ保持 Runbook (T748)

作成日: 2026-06-14  
最終更新: 2026-06-27
担当レーン: VSCode + Codex  
対象: Firebase Hosting / Google Cloud Logging / リポジトリ内 JSONL・`.log` 監査ログ

## 目的

本番アクセスログとローカル/CI生成ログを分けて管理し、ディスク枯渇、不要な長期保持、障害調査時の証跡欠落を防ぐ。Firebase Hosting のアクセスログはサーバーディスクではなく Google Cloud Logging 側の保持設定で制御し、リポジトリ内の監査 JSONL や一時 `.log` は `scripts/rotate_runtime_logs.py` で週次圧縮・世代削除する。

## 公式ドキュメント確認

2026-06-14 に以下を確認した。

- Firebase Hosting custom domains: カスタムドメイン接続と SSL 証明書自動発行の扱い
- Google Cloud Logging log buckets: `_Default` などの保持期間は `gcloud logging buckets update BUCKET_ID --location=LOCATION --retention-days=RETENTION_DAYS` で更新可能。保持期間は 1-3650 日。
- OpenAI Codex best practices / AGENTS.md: 1 セッション 1 coherent unit、リポジトリルールの明文化、作業単位ごとの検証。
- Anthropic Claude Code / Google Gemini / Supabase / GitHub / Slack / Notion などの現行 docs: 本セッションの運用ルール確認。

## 保持方針

| ログ種別 | 管理場所 | 保持 | 圧縮/削除 |
| --- | --- | --- | --- |
| Firebase Hosting アクセスログ | Google Cloud Logging `_Default` | 30日を明示 | Cloud Logging bucket retention で自動削除 |
| 障害調査用の長期証跡 | 必要時に Cloud Logging sink / GCS | 90日以上は個別判断 | GCS lifecycle policy で管理 |
| `data/audit/*.jsonl` | ローカル/CI | 7日経過または10MB超で圧縮 | `data/log_archive/YYYY/MM/*.gz` へ移動、90日で削除 |
| `data/external_api_usage*.jsonl` | ローカル/CI | 同上 | 同上 |
| `logs/*.log`, `logs/*.jsonl`, repo直下 `*.log` | ローカル/CI | 同上 | 同上 |

## T847 全テーブル保持・削除照合との接続

T847で、アプリDB、営業メールAI、社内アンケート、勤怠、サポート、課金、セルフエクスポートを含む保持・削除・匿名化マトリクスを [DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md) に追加した。本Runbookはログ/監査証跡の保持正本として、次を保証する。

| 対象 | 保持/削除の扱い | 禁止事項 |
| --- | --- | --- |
| 営業メールAIの処理ログ | `email_parse_runs` は件数、モデル名、fallback、error summaryのみを90日標準で保持 | 実メール本文、送信者メール実値、OAuth tokenを保存しない |
| 勤怠CSV解析ログ | `attendance_timesheet_imports` はdigest、拡張子、集計値、承認statusのみ保持 | CSV原本、元ファイル名、生明細を保存しない |
| 社内アンケートログ | `employee_assessment_responses` は匿名keyとredacted memoのみ保持 | 氏名、社員番号、心理/健康スコア、医療情報を保存しない |
| サポート/フィードバック | 管理summaryは抜粋だけ返し、必要に応じ180日後に匿名化 | 問い合わせ本文全文をSheets/Issue/NotebookLMへ転載しない |
| Stripe Portal | アプリ側は短命session URLを永続化しない | `STRIPE_SECRET_KEY`、カード番号、顧客ID実値をdocs/Sheetsへ記録しない |

削除請求の証跡は、削除日時、担当者、対象キー種別、成功/失敗のみを残し、削除対象の個人データ実値はログへ書かない。

## Firebase / Google Cloud 側の設定

本番プロジェクトで Cloud Logging の `_Default` bucket を 30 日保持に明示する。

```powershell
gcloud logging buckets update _Default --location=global --retention-days=30
gcloud logging buckets describe _Default --location=global
```

監査・法務・障害対応で 30 日を超える証跡が必要になった場合は、Logging sink を作成し private GCS bucket へエクスポートする。90 日を超える保持はコスト影響を WBS/課題管理表に登録してから実施する。

## ローカル/CI ログローテーション

dry-run:

```powershell
python scripts/rotate_runtime_logs.py --dry-run
```

実行:

```powershell
python scripts/rotate_runtime_logs.py
```

主なデフォルト:

| 項目 | 値 |
| --- | --- |
| 対象 | `data/audit/*.jsonl`, `data/external_api_usage*.jsonl`, `logs/*.log`, `logs/*.jsonl`, `*.log` |
| 圧縮条件 | 7日以上経過または10MB以上 |
| アーカイブ | `data/log_archive/YYYY/MM/*.gz` |
| アーカイブ保持 | 90日 |
| レポート | `exports/log_rotation_report.json` |

Windows Task Scheduler で週次実行する場合の例:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "cd C:\Users\kanta\GitHub\mighty-link-ai-connect; .\venv\Scripts\python.exe scripts\rotate_runtime_logs.py"
```

GitHub Actions 側では `.github/workflows/runtime-log-retention.yml` が週次 dry-run を実行し、スクリプト破損を検知する。実際の本番アクセスログ保持は Cloud Logging bucket retention が正本。

## 運用チェックリスト

- 週次: `Runtime Log Retention Check` workflow が成功している。
- 月次: `exports/log_rotation_report.json` に候補・削除対象が記録され、想定外の巨大ログがない。
- 障害時: `docs/INCIDENT_POSTMORTEM_RUNBOOK.md` に従い、必要な Cloud Logging クエリとローカル監査ログを incident evidence に添付する。
- コスト増の兆候: Cloud Logging retention を 30 日超へ伸ばす前に課題管理表へ登録し、責任者承認を得る。

## 関連ドキュメント

- [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md)
- [AUDIT_LOG_MASKING_AND_ENCRYPTION.md](AUDIT_LOG_MASKING_AND_ENCRYPTION.md)
- [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md)
- [DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md)
- [WBS.md](WBS.md)
