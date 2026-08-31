# Firebase / Supabase ステージング環境運用 Runbook (T788)

作成日: 2026-06-11  
オーナー: Codex レーン  
関連: [FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md) / [FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md](FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md) / [SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md](SUPABASE_DATABASE_PHYSICAL_AND_INDEX_DESIGN.md) / [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## 目的

本番反映前に、Firebase Hosting preview channel と Supabase staging 環境で変更を検証し、production の JWT secret・DB・service role key と混在しない状態を保証する。T788 の完了条件は次の3点とする。

1. Firebase Hosting preview channel の手順と禁止事項が明文化されている。
2. Supabase staging/prod の URL・anon key・JWT secret fingerprint・service role key の分離を検証できる。
3. WBS/Sheets/Calendar/GitHub Issue/Project に完了証跡を残せる。

## 公式docs確認メモ

2026-06-11 の作業開始時に、Firebase Hosting preview channel、Firebase CLI、Supabase Branching、Supabase Local Development、Supabase RLS の公式docsを確認した。反映した運用ルールは次の通り。

- Firebase Hosting の preview channel は本番の live channel へ出さずにURL付きの一時検証環境を作る用途に使う。
- Firebase CLI は Application Default Credentials またはサービスアカウントを優先し、legacy token 依存を増やさない。
- Supabase Branching は staging/QA/dev の persistent branch と、PR向けの ephemeral preview branch を使い分ける。
- Supabase branch は独立したAPI credentialsを持つため、staging/prod の URL・キー・JWT secret fingerprint を同一にしない。
- Supabase RLS はユーザーが編集可能な `user_metadata` クレームを認可判断に使わない。Firebase UID 連携は既存設計どおり `public.firebase_uid()` とサーバー側検証を正とする。

## 環境マトリクス

| 環境 | Firebase | Supabase | 用途 | データ |
| --- | --- | --- | --- | --- |
| local | Firebase Emulator / local FastAPI | Supabase Local CLI | 開発・単体検証 | synthetic seed のみ |
| staging | Firebase Hosting preview channel `staging` | Supabase persistent branch または検証用プロジェクト | 本番反映前の結合検証 | 本番個人データのコピー禁止 |
| production | Firebase Hosting live channel / Cloud Run / Functions | Supabase production project | CEO共有URLと本番運用 | 本番データ |

## 必須環境変数

値そのものはリポジトリに保存しない。fingerprint は `sha256:<短縮値>` のような非秘密値だけを記録してよい。

| 変数 | 用途 | ルール |
| --- | --- | --- |
| `FIREBASE_PROJECT_ID` | production Firebase project | `.firebaserc` の default と一致させる |
| `FIREBASE_STAGING_PROJECT_ID` | 専用staging projectを使う場合 | production と同一禁止 |
| `FIREBASE_HOSTING_PREVIEW_CHANNEL` | preview channel名 | 未設定時は `staging`、`live/prod/production/main/master/default` 禁止 |
| `FIREBASE_FUNCTIONS_DEPLOY_ENABLED` | Functions deploy opt-in | staging検証中は原則未設定/false |
| `ALLOW_STAGING_FUNCTIONS_DEPLOY` | Functions deploy二重確認 | `FIREBASE_FUNCTIONS_DEPLOY_ENABLED=true` の時だけ `true` にする |
| `SUPABASE_STAGING_URL` / `SUPABASE_PROD_URL` | Supabase endpoint | 同一禁止 |
| `SUPABASE_STAGING_ANON_KEY` / `SUPABASE_PROD_ANON_KEY` | browser向けanon key | 同一禁止 |
| `SUPABASE_STAGING_JWT_SECRET_FINGERPRINT` / `SUPABASE_PROD_JWT_SECRET_FINGERPRINT` | JWT secret比較用fingerprint | 同一禁止、raw secret保存禁止 |
| `SUPABASE_STAGING_SERVICE_ROLE_KEY` / `SUPABASE_PROD_SERVICE_ROLE_KEY` | backend secret | 同一禁止、ローカル常駐は不要 |

## 事前検証

staging deploy またはDB migration前に必ず実行する。

```powershell
python scripts/verify_staging_environment_config.py --fail-on-critical
```

JSONで監査ログを残す場合:

```powershell
python scripts/verify_staging_environment_config.py --json --output reports/staging_environment_config.json
```

`warning` は「本番事故には直結しないが、staging接続情報が未設定」を表す。`critical` は deploy/migration を止める。

## Firebase Hosting preview channel 手順

1. 変更をローカルで検証する。

```powershell
python -m pytest
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

2. preview channel名を固定する。

```powershell
$env:FIREBASE_HOSTING_PREVIEW_CHANNEL = "staging"
```

3. staging設定チェックを通す。

```powershell
python scripts/verify_staging_environment_config.py --fail-on-critical
```

4. Hostingだけをpreview channelへ出す。Functionsは opt-in まで含めない。

```powershell
firebase hosting:channel:deploy $env:FIREBASE_HOSTING_PREVIEW_CHANNEL --project $env:FIREBASE_PROJECT_ID --expires 7d
```

5. preview URLで認証・APIなし表示・主要CTAを確認する。CEO共有URLは GitHub Pages のままなので、preview URLをCEOに恒久共有しない。

6. 不要になったpreview channelは削除する。

```powershell
firebase hosting:channel:delete $env:FIREBASE_HOSTING_PREVIEW_CHANNEL --project $env:FIREBASE_PROJECT_ID
```

## Supabase staging運用

Supabaseは次の優先順位で staging を確保する。

1. Supabase Branching の persistent branch を staging/QA/dev 用に作成する。
2. Branchingを使えない場合は検証用プロジェクトを別途作成する。
3. Pull requestごとの短命検証は ephemeral preview branch を使い、完了後に削除する。

運用ルール:

- production の personal data を staging へコピーしない。必要なデータは synthetic seed と匿名化サンプルで作る。
- migration は local -> staging -> production の順に進める。
- staging migration後に `tests/test_rls_policies.py` と関係するAPIテストを通す。
- `service_role` key は Cloud Functions / Cloud Run / CI のsecret storeにのみ置き、フロントエンド・docs・WBS・Sheetsには書かない。
- RLS policyは `user_metadata` を参照しない。ユーザー属性による認可が必要な場合は、改変不能な app metadata またはDB側のロールテーブルを使う。

## 本番反映前チェックリスト

- [ ] `python scripts/verify_staging_environment_config.py --fail-on-critical` が critical なし。
- [ ] Firebase preview channel URLで主要画面が表示できる。
- [ ] Functions deploy は `FIREBASE_FUNCTIONS_DEPLOY_ENABLED=true` と `ALLOW_STAGING_FUNCTIONS_DEPLOY=true` の両方が必要。
- [ ] Supabase staging/prod URL・anon key・JWT secret fingerprint が一致していない。
- [ ] service role key をローカル・docs・Git差分へ出していない。
- [ ] `python -m pytest tests/test_staging_environment_config.py tests/test_rls_policies.py` が成功。
- [ ] 公開デモ guard が成功。
- [ ] WBS/Sheets/Calendar/GitHub Issue/Project を同期し、完了済みCalendarイベントは削除済み。

## ロールバック

- Hosting previewの問題は channel 削除で止める。
- staging DB migrationの問題は staging branch/projectを破棄して再作成する。productionへ未適用なら本番rollbackは不要。
- productionへ適用後に問題が出た場合は [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md) と [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) に従い、RLS・migration・公開URL影響を切り分ける。

## ツールレーン

- Antigravity + Gemini: preview URLの視覚確認、UI polish、browser-agentチェック。
- Codex: staging設定検証、Firebase/Supabase CLI、CI、WBS/Sheets/Calendar/GitHub同期。
- Claude Code: Runbookレビュー、RLS/secret分離レビュー、法務・運用チェックリスト整備。
