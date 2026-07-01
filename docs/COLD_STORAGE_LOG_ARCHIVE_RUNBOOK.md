# 監査ログ・稼働ログ コールドストレージ退避 Runbook (T773)

- 対象WBS: T773
- 完了日: 2026-07-01
- 担当レーン: VSCode + Codex
- 対象: Firebase / Google Cloud Logging 由来の運用証跡、リポジトリ内の監査JSONL、ローテーション済みログ、公開前Go/No-Go・監視・品質証跡
- 非対象: OAuth token、service account JSON、API key、DB URL、Stripe secret、実メール本文、勤怠CSV原本、WordPress/FTP認証情報、個人データ実値

## 目的

T748の短期ログローテーションとT847のデータ保持・削除方針だけでは、年間監査や障害再調査に必要な証跡を会社管理の低頻度ストレージへ移す運用が未整備だった。T773では、ローカル/CIの監査ログを安全に棚卸しし、ハッシュ付きマニフェスト、GCSライフサイクルテンプレート、任意のGCSアップロード手順を自動生成する。

このRunbookと `scripts/archive_audit_logs_to_cold_storage.py` により、WBS全完了時に「監査ログ・稼働ログの長期保存プロセスも整備済み」と判定できる。

## 公式ドキュメント確認

2026-07-01のT773実装で、次の公式情報を確認した。

- Google Cloud Storage Object Lifecycle Management: `SetStorageClass` でNearline/Coldline/Archiveへ遷移できることを確認。
- Google Cloud Storage storage classes: Coldlineは四半期に1回程度以下の参照、Archiveは年1回未満の参照を想定する低頻度保存向けであることを確認。
- Google Cloud Logging routing: Log RouterとsinkでログをCloud Storage等へルーティングできるが、sink作成前のログは遡及ルーティングされないことを確認。
- Firebase Functions logging: FunctionsログはCloud Loggingで閲覧・分析し、構造化ログを利用できることを確認。
- Supabase Logs: Logs Explorerの保持期間は料金プランに依存するため、本プロジェクトの長期監査証跡はアプリ側の最小化ログと会社GCSで補完する方針。
- GitHub Actions artifacts: artifactには `retention-days` を設定できるが、長期監査保存の正本はGitHub artifactではなく会社GCSに置く。
- Google Sheets API batchUpdate: WBS/課題/QA同期は既存のbatchUpdate方針を継続する。
- OpenAI Codex / AGENTS.md、Claude Code security、Gemini models/cache: セッションルール、secret非記録、モデル/ツール境界を再確認した。

## 実装成果物

| 種別 | パス | 役割 |
| --- | --- | --- |
| アーカイブスクリプト | `scripts/archive_audit_logs_to_cold_storage.py` | 対象ログ収集、SHA-256マニフェスト、ZIP作成、GCS URI検証、任意アップロード |
| テスト | `tests/test_cold_storage_log_archive.py` | secretファイル除外、manifest/zip生成、manifest-only、GCS URI検証、Runbookリンクを検証 |
| ローカル出力 | `exports/cold_storage/` | `cold_storage_manifest_YYYY-MM-DD.json` と `gcs_lifecycle_policy_template.json` |
| 上位Runbookリンク | `docs/LOG_ROTATION_AND_RETENTION_RUNBOOK.md` | T748短期ローテーションからT773長期退避へ接続 |

## 対象ログ

既定では次を収集対象にする。存在しないファイルは無視する。

| パターン | 用途 |
| --- | --- |
| `data/audit/*.jsonl` | ローカル監査イベント |
| `data/log_archive/**/*.gz` | T748で圧縮済みのローカルログ |
| `data/security_log.tsv`, `data/deploy_log.tsv` | セキュリティ/デプロイ証跡 |
| `data/external_api_usage.jsonl` | 外部API利用集計ログ |
| `exports/log_rotation_report.json` | T748のローテーション証跡 |
| `exports/issue_qa_blocker_audit.*` | 課題/QAブロッカー棚卸し |
| `exports/production_go_no_go_review.*` | 公開前Go/No-Go証跡 |
| `exports/uptime_monitor_report.json`, `exports/custom_domain_dns_diagnostic.*` | 死活監視/DNS診断証跡 |
| `exports/firebase_hosting_headers_review.*`, `exports/external_pentest_review*` | セキュリティhardening証跡 |
| `exports/secret_rotation_report.json`, `exports/infra_monitoring_dashboard.*` | secret/監視証跡 |
| `exports/monthly_quality_*.json`, `exports/weekly_cost_*.json` | 品質・コスト運用証跡 |

## 保存禁止

次はアーカイブ対象から除外する。

- `authorized_user.json`
- `client_secret.json`
- `credentials.json`
- `service-account.json`
- `.env`, `.env.local`
- `.claude/settings.local.json`
- `CLAUDE.local.md`
- SQLite/DBスナップショット
- 実メール本文、勤怠CSV原本、添付ファイル原本、API token、OAuth refresh token、Stripe secret、Supabase service role key、Firebase service account JSON

スクリプトは既知のsecretファイル名を除外し、小さなテキストファイルにsecret-like値がある場合は `secret_scan_warnings` に記録する。警告がある状態では `--upload` を拒否し、人間レビューを必須にする。

## ローカル実行

manifestだけを作る場合:

```powershell
python scripts/archive_audit_logs_to_cold_storage.py --archive-date 2026-07-01 --manifest-only
```

ZIPも作る場合:

```powershell
python scripts/archive_audit_logs_to_cold_storage.py --archive-date 2026-07-01
```

出力:

- `exports/cold_storage/cold_storage_manifest_2026-07-01.json`
- `exports/cold_storage/gcs_lifecycle_policy_template.json`
- `exports/cold_storage/mighty-link-log-archive-2026-07-01.zip`（`--manifest-only`なしの場合）

## GCS設定方針

本番のGCS bucketはT823/T850で会社所有GCPプロジェクトと請求先へ移した後に作成する。個人アカウントのbucketへ監査証跡を恒久保存しない。

推奨設定:

| 項目 | 方針 |
| --- | --- |
| bucket | 会社所有GCPプロジェクトのprivate bucket |
| location | `asia-northeast1` など会社のデータ所在地方針に合わせる |
| access | Uniform bucket-level access、有効な最小IAM |
| public access | 公開禁止 |
| lifecycle | 30日後Coldline、365日後Archive、2555日後削除 |
| encryption | Google-managed encryptionまたは会社KMS。CMEK採用時は鍵ローテーションRunbookへ接続 |
| object prefix | `mighty-link/log-archives/YYYY-MM-DD/` |

bucket作成例:

```powershell
gcloud storage buckets create gs://<company-bucket> --location=asia-northeast1 --uniform-bucket-level-access
gcloud storage buckets update gs://<company-bucket> --lifecycle-file=exports/cold_storage/gcs_lifecycle_policy_template.json
```

アップロード例:

```powershell
python scripts/archive_audit_logs_to_cold_storage.py --archive-date 2026-07-01 --gcs-uri gs://<company-bucket>/mighty-link/log-archives/2026-07-01/ --upload
```

## Cloud Logging sink接続

Firebase Hosting / Functionsの本番ログはCloud Logging側にある。長期保管が必要なログは、T823/T850の会社GCP権限移管後に、Logging sinkで会社GCS bucketへルーティングする。

注意:

- sinkは作成後に届くログをルーティングする。過去ログの遡及ルーティングは前提にしない。
- `_Default` の保持期間はT748の30日方針を維持する。
- 30日超の保持が必要なログだけをsink対象にし、コスト増は課題管理表へ記録して承認を得る。
- 実メール本文、CSV原本、secretをCloud Loggingへ出さない。必要な場合もredacted eventとhashだけにする。

## 運用頻度

| 頻度 | 手順 |
| --- | --- |
| 月次 | `--manifest-only` を実行し、対象ログ、除外、secret-like警告を確認 |
| 四半期 | ZIP生成とGCS転送のdry-run、bucket lifecycleとIAMの確認 |
| 年次 | 実ZIPを会社GCSへ保存し、マニフェストSHA-256とオブジェクト存在を確認 |
| 障害/監査時 | incident IDまたは監査IDをmanifestメモへ残し、必要なログだけ追加prefixへ保存 |

## 受け入れ条件

- `scripts/archive_audit_logs_to_cold_storage.py` がmanifest、lifecycle template、任意ZIPを生成できる。
- `--upload` は `gs://` URI指定時だけ動く。
- 既知のsecretファイル名、ローカルOAuth、service account JSON、DBスナップショットを含めない。
- secret-like値の警告がある状態ではGCSアップロードを拒否する。
- pytestでスクリプトとRunbookリンクを検証する。
- `data/WBS.tsv` と `docs/WBS.md` でT773を完了にする。

## T849への申し送り

T773完了により、長期保守・拡張フェーズの「監査ログ・稼働ログの長期保存プロセス」は完了扱いにできる。ただし、会社GCS bucketの実作成と権限移管はT823/T850、サイト開発完了総合判定はT849、販売URL復旧はT855/PUBLIC-16に残る。一般公開・有償ローンチは引き続きNo-Go。

## 関連ドキュメント

- [LOG_ROTATION_AND_RETENTION_RUNBOOK.md](LOG_ROTATION_AND_RETENTION_RUNBOOK.md)
- [AUDIT_LOG_MASKING_AND_ENCRYPTION.md](AUDIT_LOG_MASKING_AND_ENCRYPTION.md)
- [DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md)
- [AI_SAAS_SERVICE_FREEZE_RUNBOOK.md](AI_SAAS_SERVICE_FREEZE_RUNBOOK.md)
- [WBS.md](WBS.md)
