# 本番リリース ロールバック手順書 (T812)

作成日: 2026-06-13  
オーナー: VSCode + Codex レーン  
レビュー補助: VSCode + Claude Code レーン  
関連: [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) / [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md) / [WBS_PROCESS_COVERAGE_AUDIT_2026-06-13.md](WBS_PROCESS_COVERAGE_AUDIT_2026-06-13.md)

---

## 1. 目的

本書は Mighty Skill-Bridge の本番リリース後に重大な不具合が出た場合、Firebase Hosting、Firebase Functions / Cloud Run API、Supabase DB migration を安全に戻すための標準手順を定義する。T746 Go/No-Go 判定では、本書の確認と当日ロールバック担当者の明示を必須条件にする。

2026-06-13 時点の公式 Docs 確認結果:

- Firebase Hosting は live channel の Release history から過去リリースへロールバックでき、preview/staging channel から live へ同一 version を clone できる。
- Firebase / Google Cloud Run は旧 revision へ traffic を戻せる。Firebase Functions は Emulator Suite での事前検証と再デプロイを基本にする。
- Supabase の `migration repair --status reverted` は migration 履歴テーブルの修正だけであり、SQL やデータを巻き戻す操作ではない。
- GitHub Projects は Issue / ProjectV2 を API または `gh project` で同期できる。本プロジェクトでは Project #1 `Mighty Skill-Bridge` を使う。

## 2. 適用範囲

対象:

- Firebase Hosting live channel `mighty-link-ai-connect-13d22`
- Firebase Hosting rewrite 先の Cloud Run service `api` in `us-central1`
- Firebase Functions runtime `python312`
- Supabase production project の schema migration / RLS / data
- CEO 共有 URL `https://kanta13jp1.github.io/mighty-link-ai-connect/`
- カスタムドメイン / 販売 URL `https://mightylink-app.com/`（T740_3 完了済み）

対象外:

- 本番障害のエスカレーション全体。連絡網とP1/P2基準は [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) を使う。
- staging だけの失敗。preview channel削除やstaging branch破棄は [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md) を使う。

## 3. ロールバック開始条件

次のいずれかに該当したら、ロールバック判定を開始する。

| 条件 | 例 | 初期判断 |
| --- | --- | --- |
| P1 | 本番デモ/販売URLが全面停止、データ破壊リスクあり | 即時 rollback / traffic 切戻し |
| P2 | ログイン、診断API、保存処理、課金導線の主要機能が失敗 | 30分以内に forward fix 不可なら rollback |
| P3 | 一部UI崩れ、遅延、非主要機能の失敗 | hotfix 優先、必要なら Hosting rollback |
| DB破壊疑い | migration後にテーブル/RLS/データ整合性が壊れた | 書き込み停止、backup/PITR優先 |

ロールバック前に必ず残す記録:

- 影響開始時刻、検知時刻、判断者
- 対象 commit / GitHub Actions run / Firebase release / Cloud Run revision
- Supabase migration version と直近 backup/PITR 時刻
- 影響範囲とユーザー告知要否

## 4. 共通手順

1. 変更凍結を宣言する。
   - GitHub Issue に `rollback` / `incident` ラベルを付ける。
   - 以後の push / deploy / migration はロールバック担当者だけが実行する。
2. 現状を採取する。
   ```powershell
   git status --short --branch
   git log --oneline -10
   gh run list --limit 5
   firebase hosting:channel:list --project mighty-link-ai-connect-13d22
   supabase migration list --linked
   ```
3. 影響面を分ける。
   - 静的UI/HTMLだけ: Firebase Hosting rollback。
   - APIだけ: Cloud Run revision traffic rollback または Functions再デプロイ。
   - DB schema/data: 書き込み停止、backup/PITR、forward migrationまたは復元。
4. rollback後に確認する。
   ```powershell
   python -m pytest
   python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
   Invoke-WebRequest -Uri "https://mightylink-app.com/" -TimeoutSec 15 -UseBasicParsing
   ```
   T740_3 完了後は `mightylink-app.com` も strict HTTPS 成功を本番判定条件に含める。
5. WBS / Sheets / Calendar / GitHub Issue / Project を同期する。
   ```powershell
   python scripts/verify_google_workspace_account.py
   python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
   python scripts/sync_wbs_to_calendar.py
   ```

## 5. Firebase Hosting rollback

### 5.1 Consoleで直前の安定版へ戻す

1. Firebase Console で `mighty-link-ai-connect-13d22` を開く。
2. Hosting and Serverless > Hosting > `mighty-link-ai-connect-13d22` の Release history を開く。
3. 直前の known-good release の version ID、デプロイ時刻、commit を記録する。
4. 対象 release のメニューから Roll back を実行する。
5. Release history に新しい release が作成され、旧 version ID を指していることを確認する。

### 5.2 CLIで検証済みpreview/stagingをliveへ昇格する

staging preview channel で確認済みの version を本番へ出す場合だけ使う。

```powershell
$env:FIREBASE_PROJECT_ID = "mighty-link-ai-connect-13d22"
$env:FIREBASE_SITE_ID = "mighty-link-ai-connect-13d22"
firebase hosting:channel:list --project $env:FIREBASE_PROJECT_ID
$sourceChannel = "$($env:FIREBASE_SITE_ID):staging"
$targetChannel = "$($env:FIREBASE_SITE_ID):live"
firebase hosting:clone $sourceChannel $targetChannel --project $env:FIREBASE_PROJECT_ID --non-interactive
```

注意:

- preview channel は public URL なので、秘密情報や本番個人データを載せない。
- `staging` channel が存在しない場合は Console rollback を使う。
- rollback後も Git は必ず `git revert <bad_commit>` または hotfix commit で本線を安定版へ合わせる。

## 6. Firebase Functions / Cloud Run API rollback

本リポジトリの `firebase.json` は `/api/**`、`/admin/**`、`/exports/**` を Cloud Run service `api` in `us-central1` へ rewrite している。GitHub Actions の deploy workflow は、既定では `hosting` のみを deploy し、Functions deploy は `FIREBASE_FUNCTIONS_DEPLOY_ENABLED=true` のときだけ許可する。

### 6.1 Cloud Run revision trafficを旧revisionへ戻す

APIだけが壊れ、旧revisionが残っている場合の最短手順。

```powershell
$env:GCP_PROJECT_ID = "mighty-link-ai-connect-13d22"
$env:CLOUD_RUN_REGION = "us-central1"
$env:CLOUD_RUN_SERVICE = "api"
gcloud run revisions list --service $env:CLOUD_RUN_SERVICE --region $env:CLOUD_RUN_REGION --project $env:GCP_PROJECT_ID
gcloud run services update-traffic $env:CLOUD_RUN_SERVICE --to-revisions <KNOWN_GOOD_REVISION>=100 --region $env:CLOUD_RUN_REGION --project $env:GCP_PROJECT_ID
```

確認:

```powershell
gcloud run services describe api --region us-central1 --project mighty-link-ai-connect-13d22 --format "value(status.traffic)"
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

### 6.2 Functionsを既知の安定commitから再デプロイする

Functionsを触ったreleaseが原因の場合だけ実行する。Secretsが不足したまま deploy すると runtime env を消す危険があるため、CIの `FIREBASE_FUNCTIONS_DOTENV` と `FIREBASE_FUNCTIONS_DEPLOY_ENABLED` を確認してから進める。

```powershell
git fetch origin
git checkout <KNOWN_GOOD_COMMIT>
python -m pytest
firebase deploy --project mighty-link-ai-connect-13d22 --only functions --non-interactive
git checkout main
git revert <BAD_COMMIT>
git push origin main
```

CI経由で戻す場合は `git revert <BAD_COMMIT>` を main へ push し、Actions の deploy run が成功するまで監視する。

## 7. Supabase DB migration rollback

### 7.1 原則

- 本番DBでは「自動 down migration」を前提にしない。
- 破壊的変更は、migration適用前に backup/PITR 時刻と復元担当を明示する。
- schemaだけの軽微な誤りは、原則として forward fix migration を作る。
- data loss またはRLS事故は、書き込み停止、PITR/backup復元、事後検証を優先する。
- `supabase migration repair --status reverted <version>` は履歴修正のみ。SQLを戻すために使わない。

### 7.2 migration前の必須チェック

```powershell
supabase migration list --linked
supabase db reset
python -m pytest tests/test_rls_policies.py
python scripts/verify_staging_environment_config.py --fail-on-critical
```

production適用前に記録するもの:

- `supabase/migrations/<timestamp>_*.sql`
- 適用前の `supabase migration list --linked`
- backup/PITR の最終復元可能時刻
- RLS変更の影響テーブルと検証クエリ

### 7.3 schemaのみの不具合

1. 書き込み停止が必要か判断する。
2. 新しい forward fix migration を作る。
   ```powershell
   supabase migration new fix_<incident_id>
   ```
3. local/stagingで `supabase db reset` とRLS/APIテストを通す。
4. productionへ適用し、WBS/Issueへ migration version を記録する。

### 7.4 data loss / destructive migration

1. API書き込みを止める。必要なら Cloud Run traffic を旧revisionへ戻す。
2. Supabase Dashboard の Backups / PITR で復元先時刻を決める。
3. 既存productionへ直接復元するか、復元用projectを作って接続先を切り替えるかを人間ゲートで決める。
4. 復元後、RLS、件数、主要診断フロー、公開デモguardを通す。
5. migration履歴が実DB状態とずれた場合だけ、DB状態を確認したうえで履歴を修正する。
   ```powershell
   supabase migration repair --status reverted <migration_timestamp> --linked
   supabase migration list --linked
   ```

## 8. T746 Go/No-Go チェック追加

T746 の Go 判定では次を全て満たす。

- 本書の最新版を確認済み。
- rollback担当者、連絡先、実行権限が明確。
- Firebase Hosting known-good release / version ID を控えている。
- Cloud Run `api` の直前revisionを控えている。
- Supabase backup/PITR 時刻と migration list を控えている。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` が成功。
- `https://mightylink-app.com/` のHTTPS確認も成功。
- WBS / Sheets / Calendar / GitHub Issue / Project の同期担当が決まっている。

## 9. 記録テンプレート

```markdown
## Rollback record

- Incident ID:
- 発生日:
- 判断者:
- 実行者:
- 影響範囲: Hosting / API / Functions / Supabase / DNS / Billing
- Bad commit:
- Known-good commit:
- Firebase release / version ID:
- Cloud Run service / revision:
- Supabase migration version:
- Backup / PITR target:
- 実行した手順:
- 検証結果:
- GitHub Issue:
- GitHub Project item:
- Sheets/Calendar同期:
- 残課題:
```

## 10. 完了条件

- 本書が docs に追加されている。
- [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) と [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md) から参照できる。
- `data/WBS.tsv` と [WBS.md](WBS.md) で T812 が完了になっている。
- Sheets / Calendar へ同期され、完了済みCalendarイベントが削除されている。
- GitHub Issue / Project にT812完了の証跡がある。

## 11. T741 バックアップ/リストア参照

Supabase DB の日次バックアップ、GCS退避、7世代管理、復元 dry-run / 実復元の標準手順は [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) を正とする。破壊的 migration や data loss を伴う rollback では、production 直接復元の前に新規 Supabase project への復元検証を行い、GitHub Issue / WBS / Sheets に backup snapshot と判断者を記録する。
