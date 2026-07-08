# 権限棚卸し監査ログ (T850_1)

- レポートID: `ACCESS_INVENTORY_AUDIT_T850_1` / 実施日: 2026-07-08
- 判定: **ok** (10/10 仮説PASS)
- システム総数: 16（うちクリティカル 8）
- **単一障害点(SPOF・バス係数1のクリティカル): 8件** → domain_onamae, firebase_hosting, firebase_functions, gcp_iam_billing, supabase, github_repo, github_actions_secrets, google_workspace
- 会社管理済み: google_workspace, notebooklm
- 個人アカウント(移管待ち): domain_onamae, firebase_hosting, firebase_functions, gcp_iam_billing, supabase, github_repo, github_actions_secrets, stripe, claude_code, codex, antigravity, slack, notion, obsidian

> 単一障害点(SPOF)はバス係数=1のクリティカルシステムで、現状(移管前)は想定内。T823会社移管と引継ぎリハーサルでbackup所有者を確立して解消する。

## 10仮説検証

| # | 仮説 | 結果 | 根拠 |
| --- | --- | --- | --- |
| H1 | 移管runbookのクリティカル領域が全て棚卸しに存在する | PASS | 必須8件 / 欠落=なし |
| H2 | 全システムに一次所有者(primary_owner)が定義されている | PASS | 未定義=なし |
| H3 | 全クリティカルシステムにBreak-glass/復旧docsが指定されている | PASS | 未指定=なし |
| H4 | 全システムにMFA状態が記録されている(enabled/unknown/n_a) | PASS | MFA状態が不正/未記録=なし(許可=['enabled', 'n_a', 'unknown']) |
| H5 | 移管状態(transfer_state)の値が妥当である | PASS | 移管状態が不正=なし(許可=['company_managed', 'migrating', 'n_a', 'personal']) |
| H6 | criticalityの値が妥当である | PASS | criticality不正=なし |
| H7 | バス係数=1の単一障害点(backup未設定のクリティカル)を検出できる | PASS | 単一障害点(backup未設定のcritical)=['domain_onamae', 'firebase_hosting', 'firebase_functions', 'gcp_iam_billing', 'supabase', 'github_repo', 'github_actions_secrets', 'google_workspace']（8件・T823/リハーサルの対象） |
| H8 | secretを持つシステムが全て復旧/rotation手順に紐づく | PASS | secret保持システム6件が全て復旧/rotation docsに紐づく |
| H9 | 棚卸しが参照するBreak-glass/復旧docsが全て実在する | PASS | 参照docs5種 / 実在しない=なし |
| H10 | 棚卸しTSVの整合性(列数・重複ID)が保たれている | PASS | 列数=12(12期待) 行数=16 重複ID=なし |
