# 定期運用サイクル一覧（運用カレンダー）

作成日: 2026-07-20 / 担当レーン: VSCode + Claude Code（T907）
正本: 本ファイルが「GA後に継続実施すべき定期運用」の唯一の一覧。`scripts/audit_operations_cadence.py`（T907）が毎回、必須義務の網羅・Runbookリンクの実在・定期実施Runbookの登録漏れを照合する。
関連: [運用Runbookカタログ](OPERATIONS_RUNBOOK_CATALOG.md)（何を開くかの索引）/ 本書（いつ誰がやるかの暦）

> [!IMPORTANT]
> **新しい定期運用を追加したら、必ず本カレンダーへ1行追加すること。**
> 定期実施を宣言する Runbook がここに未登録だと、CIガードが「未登録」として検知して失敗する。
> 逆に、他Runbookの頻度に言及しているだけのRunbookは、ガードの除外リスト（理由付き）で対象外にしている。

---

## 日次

| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| 本番DBバックアップ（7世代保管・GCS退避） | Codex（自動） | [Supabase バックアップ・リストア](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) | 最新世代が当日分で存在し、失敗通知が無いことを確認 |

## 週次

| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| 課金・コスト配分の確認（予算上限との対比） | 人間 + Codex | [週次コストダッシュボード](WEEKLY_COST_DASHBOARD_RUNBOOK.md) | ダッシュボードが当週分を出力し、予算超過アラートが無いことを確認 |
| パフォーマンス診断 dry-run（遅延クエリ・インデックス） | Codex | [パフォーマンス診断・インデックス最適化](PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md) | dry-run が完了し、新規の重大な劣化が検出されないことを確認 |

## 月次

| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| 月次品質レポートの生成・配信（診断精度・NPS・コスト・稼働率） | Codex（自動）+ 人間確認 | [月次品質レポート自動配信](MONTHLY_QUALITY_REPORT_DELIVERY_RUNBOOK.md) | レポートが生成・配信され、KPI が記録されていることを確認 |
| 監査ログ・稼働ログのコールドストレージ退避 | Codex | [コールドストレージ退避](COLD_STORAGE_LOG_ARCHIVE_RUNBOOK.md) | 対象期間のログが退避され、退避記録が残ることを確認 |
| 有償公開・課金live有効化の月次レビュー（実施/延期/見送りの判断） | 人間（社長）+ Claude Code | [有償公開 Go/No-Go 意思決定パッケージ](PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md) | 判定結果が記録され、WBS（T862）・課題管理表へ反映されることを確認 |

## 四半期

| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| セキュリティ監査（静的解析・依存脆弱性・RLS・権限棚卸し） | 人間 + Codex | [四半期セキュリティ監査](SECURITY_AUDIT_RUNBOOK.md) | 監査レポートが出力され、検出事項が課題管理表へ起票されることを確認 |
| バックアップからの復旧訓練（リストア dry-run／実復元） | Codex + 人間 | [Supabase バックアップ・リストア](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) | 復元が RTO 目標内で完了し、訓練記録が残ることを確認 |

## 年次

| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| シークレット・APIキーの棚卸しとローテーション | 人間 + Codex | [Secretローテーション](SECRET_ROTATION_RUNBOOK.md) | 全キーの発行日・権限が見直され、失効・再発行の記録が残ることを確認 |
| Gemini モデル版の追従確認（非推奨・EOL の有無） | Codex | [Geminiモデル追従・移行](GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md) | 使用中モデルが現行サポート内であることを確認（`scripts/audit_gemini_model_policy.py`） |

---

## 事象駆動（定期ではないが発生時に必ず実行するもの）

定期実施ではないため上表には含めないが、発生時は該当Runbookに従う。

- 本番障害・DR発動 → [ディザスタリカバリ・エスカレーション](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md) → 事後に [ポストモーテム](INCIDENT_POSTMORTEM_RUNBOOK.md)
- リリース切り戻し → [本番ロールバック](PRODUCTION_ROLLBACK_RUNBOOK.md)
- 個人データの開示・削除請求 → [データ保持・削除・匿名化](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md)
- 問い合わせ・エスカレーション → [サポート窓口・エスカレーション](SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md)
- サービス終了の決定 → [サービス終了（EOL）・廃止計画](SERVICE_EOL_DECOMMISSIONING_PLAN.md)

*本カレンダーは T907（Claude Code）の成果物。頻度・担当の変更は本ファイルを正本として更新し、`python scripts/audit_operations_cadence.py` で整合を確認すること。*
