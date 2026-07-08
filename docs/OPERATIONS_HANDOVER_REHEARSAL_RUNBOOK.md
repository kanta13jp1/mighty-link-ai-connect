# 会社運用引継ぎリハーサル・Break-glass ランブック（T850）

- 作成日: 2026-07-08
- 対象WBS: T850（引継ぎリハーサル・権限棚卸し・Break-glass確認）/ 実装: T850_1（Claude Codeレーン巻き取り）
- 正本データ: `data/access_inventory.tsv`
- 監査スクリプト: `scripts/audit_access_inventory.py` / 証跡: `exports/access_inventory_audit.{json,md}`
- 関連: [ACCOUNT_OWNERSHIP_MIGRATION_RUNBOOK.md](ACCOUNT_OWNERSHIP_MIGRATION_RUNBOOK.md)（T818/T823）・[DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)・[SECRET_ROTATION_RUNBOOK.md](SECRET_ROTATION_RUNBOOK.md)
- 関連課題: R122（単一障害点=バス係数1のクリティカルシステム）

## 1. 目的

運用担当（現状は梅澤寛太）が不在でも、会社側の別担当がサービスを継続・復旧できる状態を、**リハーサル**で確認する。権限棚卸し（`data/access_inventory.tsv`）を正本に、各クリティカルシステムの一次/バックアップ所有者・MFA・Break-glass手順・移管状態を管理し、監査で網羅性と単一障害点を機械検証する。

## 2. 権限棚卸しの現況（2026-07-08 監査）

- システム総数 16（クリティカル 8）。
- **単一障害点（バス係数1・backup未設定のクリティカル）: 8件**（domain / firebase_hosting / firebase_functions / gcp_iam_billing / supabase / github_repo / github_actions_secrets / google_workspace）。現状は梅澤個人アカウント起点のため想定内だが、**GAの継続運用リスク**であり、T823会社移管でバックアップ所有者を確立して解消する（R122）。
- 会社管理済み: google_workspace / notebooklm（会社提供Googleアカウント）。
- 監査は `python scripts/audit_access_inventory.py --fail-on-attention` で再実行できる（10仮説・現状10/10 PASS、SPOFは件数として報告）。

## 3. 引継ぎリハーサル・シナリオ

各クリティカルシステムで「一次所有者が不在」を想定し、別担当が以下を実施できるかを机上/実地で確認する。合否を本節末尾に記録する。

| # | シナリオ | 確認内容 | 参照 |
| --- | --- | --- | --- |
| S1 | 本番障害でHosting/Functionsを戻す | 別担当が直前releaseへrollbackできる | [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md) |
| S2 | DBが破損/誤操作 | 別担当がSupabaseバックアップから復元できる（T870でCI復旧後） | [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) |
| S3 | Workspace同期が停止 | 別担当がOAuth再認証しSheets/Calendar同期を復旧できる（R121で実証済み） | [GOOGLE_WORKSPACE_OAUTH_REAUTH_RUNBOOK.md](GOOGLE_WORKSPACE_OAUTH_REAUTH_RUNBOOK.md) |
| S4 | secret漏洩の疑い | 別担当が該当secretをrotationし旧値を失効できる | [SECRET_ROTATION_RUNBOOK.md](SECRET_ROTATION_RUNBOOK.md) |
| S5 | DNS/SSL障害 | 別担当がお名前.comのDNSを移管前記録へ戻せる | [ACCOUNT_OWNERSHIP_MIGRATION_RUNBOOK.md](ACCOUNT_OWNERSHIP_MIGRATION_RUNBOOK.md) |
| S6 | GitHub/CI/CD停止 | 別担当がActions/Pages/Deploy認証を復旧できる（T852のWIF/ADC正規化後） | [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) |

## 4. Break-glass（緊急アクセス回復）原則

- 各クリティカルシステムのBreak-glass手順は `data/access_inventory.tsv` の `break_glass_doc` 列で正本docsへ紐づける（監査H3/H9で存在を検証）。
- 緊急時も**secret値をIssue・Sheets・NotebookLM・Slack/Notion本文へ貼らない**（棚卸しにも鍵値は保持しない）。
- Break-glass発動は事後にログ化し、使用したアカウント/経路の権限を点検・必要に応じrotationする。
- 会社移管後は、非常時Owner/Break-glassアカウントを**会社側で複数名管理**する（個人依存を残さない）。

## 5. 是正計画（SPOF解消）

R122の8件のSPOFは、T823（会社アカウント本移管）で各クリティカルシステムにバックアップ所有者（会社側2人目のOwner/管理者）を設定して解消する。設定後は `data/access_inventory.tsv` の `backup_owner` を更新し、`audit_access_inventory.py` のSPOF件数が0になることを完了基準とする。

## 6. 完了基準（T850）

- 権限棚卸し（`data/access_inventory.tsv`）が全クリティカル領域を網羅し監査green（達成）。
- 各クリティカルシステムにBreak-glass/復旧docsが紐づき、参照docsが実在（達成）。
- 引継ぎリハーサル・シナリオ（§3 S1-S6）を定義（達成）。**実地リハーサルの合否記録と、SPOFのbackup所有者確立（T823連動）は人間工程として残る。**
