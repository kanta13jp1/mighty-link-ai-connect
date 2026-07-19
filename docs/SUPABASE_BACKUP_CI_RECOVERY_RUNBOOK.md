# Supabase Daily Backup CI 復旧 Runbook（T870 / R116）

作成日: 2026-07-19 / 起草レーン: VSCode + Claude Code（T870_1）
実施担当: **Codex + 寛太梅澤**（GCP・GitHub Secrets 操作を伴うため人間工程）
関連WBS: T870（本復旧） / T852（Firebase CI/CD WIF 移行・同一根本原因） / T849（GAクローズ）
関連課題: **R116（HIGH・open）** / R122
関連docs: [SUPABASE_INFRA_AUDIT_2026-07-04.md](SUPABASE_INFRA_AUDIT_2026-07-04.md) / [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) / [FIREBASE_CI_CD_WIF_MIGRATION_REPORT.md](FIREBASE_CI_CD_WIF_MIGRATION_REPORT.md)
対象ワークフロー: [.github/workflows/supabase-backup.yml](../.github/workflows/supabase-backup.yml)

> [!WARNING]
> **本番DBの自動バックアップが存在しない状態です。** Supabase Daily Backup CI は 2026-06-22 以降 一度も成功していません（R116）。
> 暫定として 2026-07-04 に読み取り専用ローカル論理バックアップを取得済み（`backups/` 配下・git管理外）ですが、恒久復旧は本Runbookで行います。

> [!IMPORTANT]
> **GAクローズ上の優先度は最高です。** T849_2 の集計により、R116 単独で **4つのGAゲート（PUBLIC-02 / PUBLIC-13 / PUBLIC-14 / PUBLIC-15）** を塞いでいることが判明しています。本Runbookの完了が最短のGA前進経路です。

---

## 1. 根本原因（調査済み・再調査不要）

`docs/SUPABASE_INFRA_AUDIT_2026-07-04.md` の調査結果:

| # | 事象 | 内容 |
| --- | --- | --- |
| 1 | **WIFバインディングが旧プロジェクト** | Workload Identity Pool が **旧プロジェクト（project number `100664750415` / `mighty-link-ai-connect-d7fa2`）** 側に設定されている |
| 2 | **ロールが誤り** | `roles/iam.serviceAccountUser` が付与されている。**正しくは `roles/iam.workloadIdentityUser`** |
| 3 | **secretのproviderも旧プロジェクト参照** | `GCP_WORKLOAD_IDENTITY_PROVIDER` が旧プロジェクトのリソース名を指している可能性が高い |
| 4 | **バックアップ用GCSバケット未作成** | `SUPABASE_BACKUP_GCS_URI` の向き先が存在しない |
| 5 | **secret未登録** | `SUPABASE_DB_URL` / `SUPABASE_BACKUP_GCS_URI` が未登録 |

ワークフロー本体（`supabase-backup.yml`）に欠陥はありません。認証情報・クラウド側構成のみが原因です。

## 2. 前提条件

- 現行GCPプロジェクトの **IAM管理者権限**（Workload Identity Pool / サービスアカウント操作）
- 対象GitHubリポジトリの **Secrets 書き込み権限**（`gh secret set` または Settings → Secrets）
- `gcloud` CLI 認証済み（`gcloud auth login`）
- 本番 Supabase の接続文字列（Supavisor pooler 経由）を安全に取得できること

以下のプレースホルダを実値に置き換えて実行します（**実値は本Runbookに書き戻さないこと**）:

| プレースホルダ | 意味 |
| --- | --- |
| `<PROJECT_ID>` | 現行GCPプロジェクトID |
| `<PROJECT_NUMBER>` | 現行GCPプロジェクト番号（**旧 `100664750415` ではないこと**） |
| `<POOL_ID>` | Workload Identity Pool ID（例: `github-pool`） |
| `<PROVIDER_ID>` | OIDC Provider ID（例: `github-provider`） |
| `<SA_EMAIL>` | バックアップ実行用サービスアカウント |
| `<BUCKET>` | バックアップ用privateバケット名 |
| `<OWNER>/<REPO>` | GitHubリポジトリ |

## 3. 復旧手順

### Step 1: 現行プロジェクトの確認（旧プロジェクト誤設定の再発防止）

```bash
gcloud config get-value project
gcloud projects describe <PROJECT_ID> --format='value(projectNumber)'
```

`projectNumber` が **`100664750415` でない**ことを必ず確認します。一致した場合は旧プロジェクトを見ているため中止し、正しいプロジェクトへ切り替えます。

### Step 2: Workload Identity Pool / Provider を現行プロジェクトに作成

```bash
gcloud iam workload-identity-pools create <POOL_ID> \
  --project=<PROJECT_ID> --location=global \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc <PROVIDER_ID> \
  --project=<PROJECT_ID> --location=global \
  --workload-identity-pool=<POOL_ID> \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='<OWNER>/<REPO>'"
```

> `--attribute-condition` でリポジトリを限定します。省略すると任意のリポジトリが借用可能になるため必須です。

既に存在する場合は `describe` で issuer と attribute-condition が上記と一致するか確認します。

### Step 3: サービスアカウントへ **workloadIdentityUser** を付与（誤ロールの是正）

```bash
gcloud iam service-accounts add-iam-policy-binding <SA_EMAIL> \
  --project=<PROJECT_ID> \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<POOL_ID>/attribute.repository/<OWNER>/<REPO>"
```

> [!CAUTION]
> 今回の障害原因は **`roles/iam.serviceAccountUser` を誤って付与していた**ことです。`roles/iam.workloadIdentityUser` でなければ WIF 借用は成立しません。旧プロジェクト側に残る誤バインディングは確認のうえ削除します。

バケットへの書き込み権限も付与します:

```bash
gcloud storage buckets add-iam-policy-binding gs://<BUCKET> \
  --member="serviceAccount:<SA_EMAIL>" --role="roles/storage.objectAdmin"
```

### Step 4: バックアップ用 private GCS バケットを作成

```bash
gcloud storage buckets create gs://<BUCKET> \
  --project=<PROJECT_ID> --location=asia-northeast1 \
  --uniform-bucket-level-access --public-access-prevention
```

> `--public-access-prevention` と `--uniform-bucket-level-access` は必須です（本番DBダンプを保持するため公開厳禁）。保持世代はワークフローの `SUPABASE_BACKUP_RETENTION`（既定 7）で制御します。

### Step 5: GitHub Secrets を登録（**値はコマンドの対話入力で渡す**）

ワークフローが参照するリポジトリ secret は次の4件です:

| Secret 名 | 内容 |
| --- | --- |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<POOL_ID>/providers/<PROVIDER_ID>` |
| `GCP_SERVICE_ACCOUNT_EMAIL` | `<SA_EMAIL>` |
| `SUPABASE_BACKUP_GCS_URI` | `gs://<BUCKET>/supabase` |
| `SUPABASE_DB_URL` | 本番 Supabase 接続文字列（Supavisor pooler 経由） |

```bash
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --repo <OWNER>/<REPO>
gh secret set GCP_SERVICE_ACCOUNT_EMAIL      --repo <OWNER>/<REPO>
gh secret set SUPABASE_BACKUP_GCS_URI        --repo <OWNER>/<REPO>
gh secret set SUPABASE_DB_URL                --repo <OWNER>/<REPO>
```

> [!CAUTION]
> `gh secret set` は値を**対話入力**で受け取ります。値をコマンドライン引数・シェル履歴・docs・Sheets・NotebookLM へ残さないでください。`SUPABASE_DB_URL` は本番DBの完全な認証情報です。

### Step 6: ワークフローを手動実行して green を確認

```bash
gh workflow run "Supabase Daily Backup" --repo <OWNER>/<REPO>
gh run list --workflow="Supabase Daily Backup" --repo <OWNER>/<REPO> --limit 1
gh run watch --repo <OWNER>/<REPO>
```

`workflow_dispatch` で起動し、`Validate backup configuration` → `Authenticate to Google Cloud via WIF` → `Create backup and upload to GCS` が全て成功することを確認します。

## 4. 完了判定（T870 の受入条件）

すべて満たした時点で T870 を完了とします。

- [ ] Step 1 で現行プロジェクト番号が旧 `100664750415` でないことを確認した
- [ ] WIF Pool/Provider が現行プロジェクトに存在し、`attribute-condition` でリポジトリ限定されている
- [ ] SA に `roles/iam.workloadIdentityUser` が付与され、旧プロジェクトの誤バインディングを削除した
- [ ] private バケットが作成され、public access prevention が有効
- [ ] 上記4 secret が登録済み（値は未記録）
- [ ] `workflow_dispatch` 実行が **green**
- [ ] バケットにダンプオブジェクトが実在する（`gcloud storage ls gs://<BUCKET>/supabase`）
- [ ] 翌日のスケジュール実行（03:00 JST）も green
- [ ] **R116 を resolved へ更新**し、**PUBLIC-02 の再判定**を実施（PUBLIC-13/14/15 の `blocked_by_open_issue` 解消も併せて確認）
- [ ] `python scripts/generate_wbs_completion_evidence.py` を再実行し、R116 がゲート表から消えることを確認

## 5. 失敗時の切り分け

| 症状 | 想定原因 | 対処 |
| --- | --- | --- |
| `Missing GCP WIF configuration` で exit 2 | secret 未登録 | Step 5 を再実施 |
| WIF 認証で `Permission denied` / `unauthorized_client` | ロールが `serviceAccountUser` のまま、または provider が旧プロジェクト参照 | Step 2–3 を再確認（本障害の主因） |
| `attribute-condition` 不一致で拒否 | リポジトリ名の不一致 | Provider の condition を確認 |
| GCS アップロードで 403 | SA にバケット権限なし | Step 3 の `storage.objectAdmin` を付与 |
| DB 接続失敗 | `SUPABASE_DB_URL` が direct 接続 | Supavisor pooler 経由の文字列に差し替え |

## 6. 暫定運用（復旧までの間）

- 2026-07-04 取得のローカル論理バックアップ（`backups/` 配下・git管理外）が唯一の復旧材料です。
- 復旧完了までは本番DBスキーマの破壊的変更を避け、実施する場合は事前に手動ダンプを取得します。
- リストア手順は [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) を参照します。

## 7. セキュリティ上の注意

- 本Runbookには **secret の値を一切記載しません**（`tests/test_backup_ci_recovery_runbook.py` が値の混入を機械検証します）。
- バックアップバケットは常に private を維持します。
- 旧プロジェクト（`d7fa2`）側の不要なWIFバインディング・SAは、復旧確認後に棚卸しして削除します（R122 のバス係数是正と併せて実施）。
