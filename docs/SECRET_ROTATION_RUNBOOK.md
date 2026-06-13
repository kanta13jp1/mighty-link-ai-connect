# サードパーティAPIキー・Secretローテーション Runbook (T751)

作成日: 2026-06-14
担当レーン: VSCode + Codex
対象: Gemini / OpenAI / Anthropic / Firebase / Supabase / Slack / Notion / Stripe / その他外部連携

## 目的

APIキー、Webhook secret、DB接続文字列、service role keyを年次または短期サイクルで見直し、期限切れ・過剰権限・secret漏洩のリスクを下げる。秘密値はGit、docs、Sheets、Issue、reportへ保存せず、`data/secret_rotation_inventory.tsv` にはメタデータだけを置く。

## 公式ドキュメント確認

2026-06-14 に以下を確認した。

- GitHub Actions secrets: workflowでは `secrets` コンテキストを使い、値をログやartifactへ出さない。
- Firebase Functions environment configuration: runtime secretは環境変数またはSecret Managerで扱い、Functions deploy時に必要な値を明示する。
- Supabase docs: `service_role` key はサーバー側だけで使い、RLS前提の `anon` key と分離する。
- Slack security docs: tokenやIncoming Webhookは最小scope、漏洩時の即時revoke、rotation履歴の記録が必要。
- Stripe API docs: live/test keyとwebhook signing secretを分け、restricted keyを優先する。
- OpenAI Codex / Anthropic Claude Code / Google Gemini: agent作業は権限・外部tool・検証ログをWBS/Issueへ接続し、secretを会話や差分へ貼らない。

## 管理ファイル

| ファイル | 役割 |
| --- | --- |
| `data/secret_rotation_inventory.tsv` | secret名、provider、保管場所、owner、rotation間隔、確認方法の正本 |
| `scripts/check_secret_rotation_schedule.py` | TSVを読み、期限切れ・期限接近・secret値混入を検出してJSON reportを作成 |
| `.github/workflows/secret-rotation-review.yml` | 毎週月曜 06:15 JST にローテーション期限を確認 |
| `exports/secret_rotation_report.json` | 直近の期限チェック結果 |

## 手動実行

```powershell
python scripts/check_secret_rotation_schedule.py
```

期限切れの必須secretで失敗させる場合:

```powershell
python scripts/check_secret_rotation_schedule.py --fail-on-overdue
```

日付を固定して検証する場合:

```powershell
python scripts/check_secret_rotation_schedule.py --as-of 2026-06-14
```

## 判定ルール

| status | 意味 | 対応 |
| --- | --- | --- |
| `ok` | 次回ローテーション期限まで余裕がある | 通常運用 |
| `due_soon` | `warning_days` 以内に期限 | GitHub Issueを作り、担当者がprovider consoleで再発行予定を確定 |
| `overdue_required` | 必須secretが期限超過 | workflow失敗。即日ローテーションまたは例外承認を記録 |
| `overdue_optional` | 任意secretが期限超過 | 連携を使うならローテーション、未使用ならsecret削除 |

## ローテーション手順

1. `data/secret_rotation_inventory.tsv` の対象行を確認する。
2. provider consoleで新secretを発行する。
3. GitHub Actions secret、Firebase Functions env、GCP Secret Manager、Supabase/Stripe/Slack側設定の該当場所だけを更新する。
4. 旧secretを無効化または削除する。
5. 該当する検証を行う。
6. `rotation_anchor_date` を実施日へ更新し、WBS/課題管理表/GitHub Issueへ証跡を残す。

## Provider別確認観点

| provider | 確認観点 |
| --- | --- |
| Google Gemini | AI Studio / GCP上のkey、利用量、クォータ、不要key削除 |
| OpenAI / Anthropic / DeepSeek / Kimi / xAI / BytePlus | project単位のkey、最終利用、billing guard、未使用key削除 |
| Firebase | service account keyよりWorkload Identity Federationを優先。JSON key利用時は旧keyを削除 |
| Supabase | `service_role` はサーバー側のみ。`anon` keyはRLS有効性とセットで確認 |
| Slack | Bot token / webhook URLのscope、install先workspace、revoke手順 |
| Notion | integration secret、共有済みページ/DBの範囲 |
| Stripe | live/test分離、restricted key、webhook signing secret、再送テスト |

## Secret値混入時

`scripts/check_secret_rotation_schedule.py` がsecretらしい値を検出した場合、exit code 2で失敗する。

1. 該当差分をコミットせず削除する。
2. provider側で当該secretを即時revoke/rotateする。
3. 課題管理表へHigh以上のインシデントとして記録する。
4. [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md) に従ってポストモーテムを残す。

## 関連ドキュメント

- [SECURITY_AUDIT_RUNBOOK.md](SECURITY_AUDIT_RUNBOOK.md)
- [AUDIT_LOG_MASKING_AND_ENCRYPTION.md](AUDIT_LOG_MASKING_AND_ENCRYPTION.md)
- [FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md](FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md)
- [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md)
- [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md)
- [WBS.md](WBS.md)
