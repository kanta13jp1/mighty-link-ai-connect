# コスト・クォータ監視アラート統合ガード仕様書 (COST_QUOTA_ALERTS_GUARD.md)

- 関連WBS: `T932` (8. 本番運用・品質管理 / コスト監視)
- 担当レーン: `Antigravity + Gemini`
- 検証スクリプト: [`scripts/audit_cost_quota_alerts.py`](../scripts/audit_cost_quota_alerts.py)
- テストファイル: [`tests/test_cost_quota_alerts_audit.py`](../tests/test_cost_quota_alerts_audit.py)

---

## 1. 目的と保護対象

本ガードは、3大AIプロバイダー（Gemini, Claude, OpenAI Codex）および各種クラウドインフラ（Firebase, Supabase, Stripe, GCP）の利用において、以下のコスト管理・クォータ監視基準が遵守されていることをCI上で自動検証します。

1. **予算超過防止のサーキットブレーカー**: 予期せぬAPIコールの爆発やループ呼び出しを防ぐ日次上限・有効化フラグ（`SEEDANCE_API_ENABLED` 等）の実装。
2. **コスト・クォータ監視エンドポイント**: 管理者用ダッシュボード（`/api/admin/usage`）を通じてリアルタイムに使用量と推定コストを可視化。
3. **契約ポリシーと上限の整合性**: [`AI_COST_MONITORING_AND_QUOTA_DESIGN.md`](AI_COST_MONITORING_AND_QUOTA_DESIGN.md) に基づく月額枠と3大AIツールの定義。
4. **定期通知・監視アラート体制**: [`scripts/send_daily_report.py`](../scripts/send_daily_report.py) による日次使用量レポート送信。
5. **ストレージ費用増大防止**: [`scripts/archive_audit_logs_to_cold_storage.py`](../scripts/archive_audit_logs_to_cold_storage.py) によるコールドストレージ退避。

---

## 2. 10仮説と検証基準

| 仮説 | 検証内容 | 合格基準 |
|---|---|---|
| **H1** | コストポリシー文書 | `AI_DEVELOPMENT_TOOL_SUBSCRIPTION_POLICY.md` および価格プラン書が実在 |
| **H2** | 管理者用使用量API | `/api/admin/usage` エンドポイントが `src/app.py` に実装 |
| **H3** | 監視スクリプト群 | 日次レポート・外部API監査・ログ退避スクリプトが実在 |
| **H4** | サーキットブレーカー | 外部API呼び出しガードフラグ・日次上限機構が実装 |
| **H5** | 緊急停止Runbook | `AI_SAAS_SERVICE_FREEZE_RUNBOOK.md` が実在 |
| **H6** | Stripe連携 | `src/stripe_customer_portal.py` が実在 |
| **H7** | 3大AIツール整合性 | Gemini, Claude, OpenAI の定義・整合性を確認 |
| **H8** | ガード仕様書 | 本仕様書が実在 |
| **H9** | コールドストレージ退避 | 監査ログアーカイブスクリプトが実在 |
| **H10** | 全体健全性 | 全仮説がPASSし、ドリフトが0であること |

---

## 3. 手動実行方法

```powershell
python scripts/audit_cost_quota_alerts.py
```
