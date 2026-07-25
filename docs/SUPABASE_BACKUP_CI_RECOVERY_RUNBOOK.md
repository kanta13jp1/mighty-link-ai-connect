# Supabase Daily Backup CI 復旧・運用 Runbook（T870 / R116）

最終更新: 2026-07-25
対象: `.github/workflows/supabase-backup.yml`
関連: T741 / T771 / T852 / T870 / R116 / PUBLIC-02

## 現在の構成

2026-07-25 に、失敗し続けていた日次バックアップ経路を現行GCPプロジェクトへ再構成した。

| 項目 | 設定 |
| --- | --- |
| GCP project | `mighty-link-ai-connect-13d22`（project number `526991227996`） |
| WIF pool | `github-backup-pool` |
| WIF provider | `mighty-link-backup` |
| GitHub repository ID | `1244319528` |
| 許可ブランチ | `refs/heads/master` |
| Service account | `supabase-backup-ci@mighty-link-ai-connect-13d22.iam.gserviceaccount.com` |
| GCS bucket | `mighty-link-ai-connect-13d22-supabase-backups`（`asia-northeast1`） |
| 保存prefix | `supabase/` |
| 実行時刻 | 毎日 03:00 JST（`0 18 * * *` UTC） |

DB URLと認証情報の値はGitHub Actions Secretsだけに保存し、docs、data、Issue、ログへ記録しない。

## セキュリティ境界

- GitHub OIDCから短期資格情報を発行し、サービスアカウント鍵は作成しない。
- ProviderはGitHubの数値repository IDと`master`ブランチの両方で制限する。
- Service accountには`roles/iam.workloadIdentityUser`だけを付与する。
- Bucket権限は`roles/storage.objectCreator`と`roles/storage.objectViewer`に限定する。
- BucketはUniform bucket-level accessとPublic access preventionを有効化する。
- Object retentionは7日、lifecycle削除は30日とする。
- 本番復元は人間のGo/No-Goなしに実行しない。

旧障害の原因は、旧project number `100664750415`（`d7fa2`）側への誤った
`roles/iam.serviceAccountUser` binding、現行project側のWIF/bucket未作成、
`SUPABASE_DB_URL`と`SUPABASE_BACKUP_GCS_URI`未登録だった。

## GitHub Actions Secrets

Workflowが参照するsecret名は次の4件。

| Secret | 内容 |
| --- | --- |
| `GCP_BACKUP_WORKLOAD_IDENTITY_PROVIDER` | バックアップ専用WIF provider resource name |
| `GCP_BACKUP_SERVICE_ACCOUNT_EMAIL` | バックアップ専用service account email |
| `SUPABASE_BACKUP_GCS_URI` | private bucketの`gs://.../supabase` URI |
| `SUPABASE_DB_URL` | 本番Supabase Supavisor pooler接続文字列 |

登録済みかは値を表示せず確認する。

```powershell
gh secret list | Select-String 'GCP_BACKUP_|SUPABASE_'
```

## Bucket policy

設定ファイル: `.github/config/supabase-backup-lifecycle.json`

```powershell
gcloud storage buckets update gs://mighty-link-ai-connect-13d22-supabase-backups `
  --retention-period=P7D `
  --lifecycle-file=.github/config/supabase-backup-lifecycle.json
```

retention policyはロックしない。運用移管後に会社管理者が法務・コスト要件を確認し、必要ならロックを別承認で実施する。

## 手動実行と確認

```powershell
gh workflow run "Supabase Daily Backup" --ref master
gh run list --workflow "Supabase Daily Backup" --limit 1
```

成功条件:

1. `Validate backup configuration`が成功する。
2. `Authenticate to Google Cloud via WIF`が成功する。
3. `Create backup and upload to GCS`が成功する。
4. `Verify uploaded backup manifest`が成功する。
5. GCS上のmanifestが`status=created`で、3つのSQLファイルのSHA-256を保持する。

オブジェクトの存在確認:

```powershell
gcloud storage ls --recursive gs://mighty-link-ai-connect-13d22-supabase-backups/supabase
```

DB URL、SQL内容、manifest全文はIssueやチャットへ貼らない。

## 復元確認

本番DBへは直接戻さない。ダウンロードしたsnapshotを会社管理の新規・非本番Supabase projectへ復元し、RLS/API/公開デモguardを確認してから本番復元可否を判断する。

```powershell
$env:SUPABASE_RESTORE_DB_URL = "<non-production target>"
python scripts/restore_supabase_database.py backups/supabase/<snapshot> --dry-run
```

`restore_supabase_database.py`はmanifestにSHA-256がある場合、改ざん・破損を検出して復元を拒否する。実復元には`--confirm-restore`が必要。

## 障害切り分け

| 症状 | 確認 |
| --- | --- |
| `Missing ...` | 4つのGitHub Actions Secretsの登録日時を確認 |
| WIF `unauthorized_client` | providerのrepository ID、branch条件、`workloadIdentityUser` bindingを確認 |
| GCS 403 | bucket IAMのobjectCreator/objectViewerとservice accountを確認 |
| DB接続失敗 | Supavisor pooler接続文字列、SSL、パスワードrotationを確認 |
| checksum mismatch | そのsnapshotを使用禁止にし、直前の正常snapshotで再検証 |

## 完了・運用判定

- 手動`workflow_dispatch`がgreen。
- GCSに実バックアップ4ファイルが存在。
- synthetic snapshotの復元dry-runがgreen。
- 翌日のscheduled runもgreen。
- T870完了、R116 resolved、PUBLIC-02再判定を証跡付きで更新。

公式参照:

- Google Cloud Workload Identity Federation for deployment pipelines
- `google-github-actions/auth`
- Google Cloud Storage IAM roles
- Supabase Database Backups
