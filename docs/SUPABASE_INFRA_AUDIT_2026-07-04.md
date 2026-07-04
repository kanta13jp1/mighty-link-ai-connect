# Supabaseインフラ監査 2026-07-04（10仮説・T811/T837判定とバックアップ検証）

作成日: 2026-07-04
担当レーン: VSCode + Claude Code（Codex担当のT811を巻き取り）
関連WBS: T811（完了） / T837（完了・不要判定） / T852 / T870 / T871
関連課題/QA: R53 / R116 / R117 / QA-95
関連docs: [GO_NO_GO_DECISION_PACK_2026-07-07.md](GO_NO_GO_DECISION_PACK_2026-07-07.md) / [SUPABASE_POSTGRES_UPGRADE_RUNBOOK.md](SUPABASE_POSTGRES_UPGRADE_RUNBOOK.md) / [POSTMORTEM_2026-07-04_R114_MISSING_PROD_TABLES.md](POSTMORTEM_2026-07-04_R114_MISSING_PROD_TABLES.md)

---

## 方式

「Supabase PG アップグレードの準備状況」について反証可能な10仮説を立て、専用スクリプト・CI履歴・GCP実機・migration走査で全数検証した。

## 検証結果

| # | 仮説 | 判定 | 根拠 |
| --- | --- | --- | --- |
| H1 | 本番DBはPG14のまま（EOL超過） | **棄却（想定と真逆）** | `check_supabase_postgres_version.py --execute` で **PostgreSQL 17.6** を確認。6/13新規作成プロジェクトのため最初から最新メジャーだった。R53は実バージョン未確認のまま一般告知から立てた誤アラーム |
| H2 | staging相当環境が存在しない | 支持（許容） | SUPABASE_STAGING_DB_URLは未設定。staging相当はローカルemulatorスタック（T-局所検証）で運用しており、単一Supabaseプロジェクト構成。PG17.6のため当面のアップグレード演習は不要 |
| H3 | バックアップは準備済み | **棄却（重大な逆発見）** | **Supabase Daily Backup CIは6/22以降の全12回が失敗（＝一度も成功していない）**。原因: `SUPABASE_DB_URL`・`SUPABASE_BACKUP_GCS_URI` secret未登録、バックアップ用GCSバケット自体が未作成（R116） |
| H4 | PG17非対応の拡張を使用 | 棄却 | CREATE EXTENSION / pgjwt / plv8 / timescaledb 等の使用箇所ゼロ |
| H5 | アプリSQLにPG17非互換構文 | 棄却 | 既に17.6上で全機能動作中（本日のR114検証含む） |
| H6 | RunbookがSupabase現行手順と乖離 | 棄却（当面moot） | Runbookは将来のメジャーアップグレード用として保持。現行は17.6で最新 |
| H7 | ダウンタイム許容枠が未定義 | moot | アップグレード自体が不要 |
| H8 | pooler接続文字列の変更が必要 | 棄却 | Supavisor pooler経由で17.6へ正常接続中 |
| H9 | PG14のままではセキュリティ0パッチ | moot | 17.6のため該当せず |
| H10 | T837の人間手順が7/6までに実施不能 | moot | **T837は不要**。バージョン確認証跡（exports/supabase_postgres_version_check.json）をもって完了扱い |

## 監査中の追加発見

### R116: 本番DBバックアップパイプラインが一度も稼働していない（HIGH）

- CI失敗の直接原因: repository secretは `FIREBASE_*` と WIF 2種のみで、`SUPABASE_DB_URL`・`SUPABASE_BACKUP_GCS_URI` が未登録。GCSバケットも未作成。
- さらに深い原因: **WIFバインディングが旧プロジェクト（project number 100664750415 / mighty-link-ai-connect-d7fa2）のWorkload Identity Poolに、誤ったロール（roles/iam.serviceAccountUser。正しくは roles/iam.workloadIdentityUser）で設定されている**。secretのWIF providerも旧プロジェクトを指している可能性が高い。これはT852（Firebase CI/CD認証再構成）の根本原因とも一致する。
- **暫定対応済み（2026-07-04）**: 読み取り専用のローカル論理バックアップを取得（11テーブル・21行、`backups/supabase/`配下・git管理外）。データ量が極小の社内フェーズでは十分な暫定策。
- 恒久対応（T870、T852と連動）: 現行プロジェクトにWIFプール/プロバイダを再作成 → SAへworkloadIdentityUser付与 → バックアップ用privateバケット作成 → secret 2種登録 → workflow green確認。
- **PUBLIC-02（バックアップゲート）は「手順整備済み」でPASSとしていたが、運用実績が無いため7/7判定で再評価する。**

### R117: 6/16〜6/18のmigrationも本番未適用（HIGH）

バックアップ取得時のテーブル一覧で、本番は11テーブルのみと判明。**feedback_events、support_requests、営業メール系9テーブルが存在しない**（R114と同根。本番スキーマは〜6/15頃のinit_db実行時点で凍結されている）。フィードバック送信・サポート問い合わせ・営業メールDB保存は本番で失敗する状態。

- 対応: 冪等migration 3ファイル（IF NOT EXISTS確認済み）の適用スクリプトを用意済み。R114と同様にユーザー実行で適用する。
- 適用後、T845 UATの「本番実書き込み確認」対象へフィードバック・サポート・営業メールを追加する。

## T811/T837の完了判定

- T811: 本番PGメジャーバージョン確認（17.6）と「アップグレード計画不要」の判定をもって完了。証跡: `exports/supabase_postgres_version_check.json`。
- T837: 本番が既にPG15以上（17.6）のため実行不要と判定し完了。R53の懸念は解消。
- 将来のメジャーアップグレード時は [SUPABASE_POSTGRES_UPGRADE_RUNBOOK.md](SUPABASE_POSTGRES_UPGRADE_RUNBOOK.md) を使用する。
