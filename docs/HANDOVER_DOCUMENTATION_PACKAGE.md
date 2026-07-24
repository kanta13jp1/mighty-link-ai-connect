# 引継ぎドキュメンテーションパッケージ（Handover Documentation Package）

## 概要

本ドキュメントは、MightyLINK AI Connect（旧社内マッチング・勤怠・営業メールAI接続システム）のサービス運用および運用保守を、次期運用チームまたは他部門へ安全かつ漏れなく引き継ぐための総合引継ぎパッケージ（Handover Documentation Package）です。

全156件のドキュメント、46本の運用Runbook、23本の自動品質CIガード、および各種法務・アーキテクチャ設計書を体系化し、運用の持続可能性と品質担保を実現します。

---

## 1. ドキュメント体系とディレクトリ構造

プロジェクト内のドキュメントは `docs/` ディレクトリ配下に一元管理されており、以下の主要カテゴリに分類されます。

| カテゴリ | 概要 | 主要ドキュメント |
|---|---|---|
| **全体設計・要件定義** | システム全体のアーキテクチャ・要件 | [requirements.md](requirements.md), [database.md](database.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| **アーキテクチャ意思決定 (ADR)** | 技術選定と意思決定理由 | [ARCHITECTURE_DECISION_RECORDS.md](ARCHITECTURE_DECISION_RECORDS.md) |
| **運用Runbookカタログ** | 全46本の運用手順書インデックス | [OPERATIONS_RUNBOOK_CATALOG.md](OPERATIONS_RUNBOOK_CATALOG.md) |
| **定期運用カレンダー** | 運用タスクの周期・担当 | [OPERATIONS_CADENCE_CALENDAR.md](OPERATIONS_CADENCE_CALENDAR.md) |
| **法務・コンプライアンス** | 利用規約・プライバシー・特商法 | [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md), [PRIVACY_POLICY.md](PRIVACY_POLICY.md), [TOKUSHOHO_NOTATION.md](TOKUSHOHO_NOTATION.md) |
| **品質保証・UAT** | テスト仕様書・品質ガードカタログ | [UAT_TEST_SPECIFICATION.md](UAT_TEST_SPECIFICATION.md), [QUALITY_GUARD_CATALOG.md](QUALITY_GUARD_CATALOG.md) |
| **UI/UX・表記ガイド** | 日本語表記統一・画面ガイドライン | [JAPANESE_UI_UX_STYLE_GUIDE.md](JAPANESE_UI_UX_STYLE_GUIDE.md) |
| **社長定例・戦略アジェンダ** | 経営報告・意思決定パッケージ | [CEO_MEETING_AGENDA_2026-08-05.md](CEO_MEETING_AGENDA_2026-08-05.md), [GROWTH_STRATEGY_ROADMAP.md](GROWTH_STRATEGY_ROADMAP.md) |

---

## 2. 運用・保守手順（Runbook体系）

全46本のRunbookは [OPERATIONS_RUNBOOK_CATALOG.md](OPERATIONS_RUNBOOK_CATALOG.md) にて体系化されています。

### 2.1 ドメイン別主要Runbook
1. **DB・データ基盤**: [DB_MIGRATION_MANAGEMENT_RUNBOOK.md](DB_MIGRATION_MANAGEMENT_RUNBOOK.md), [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md)
2. **インフラ・監視・障害対応**: [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md), [UPTIME_MONITORING_AND_ALERT_RUNBOOK.md](UPTIME_MONITORING_AND_ALERT_RUNBOOK.md)
3. **セキュリティ・シークレット**: [SECRET_ROTATION_RUNBOOK.md](SECRET_ROTATION_RUNBOOK.md), [SECURITY_AUDIT_RUNBOOK.md](SECURITY_AUDIT_RUNBOOK.md)
4. **課金・コスト**: [WEEKLY_COST_DASHBOARD_RUNBOOK.md](WEEKLY_COST_DASHBOARD_RUNBOOK.md), [STRIPE_CUSTOMER_PORTAL_RUNBOOK.md](STRIPE_CUSTOMER_PORTAL_RUNBOOK.md)
5. **個人情報・データ主体対応**: [DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md](DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md), [USER_DATA_SELF_EXPORT_RUNBOOK.md](USER_DATA_SELF_EXPORT_RUNBOOK.md)
6. **営業メールAIパイプライン**: [SALES_EMAIL_EXTRACTION_PIPELINE_RUNBOOK.md](SALES_EMAIL_EXTRACTION_PIPELINE_RUNBOOK.md)

---

## 3. 定期運用スケジュール（運用カレンダー）

運用チームが定期的に実施すべき業務は [OPERATIONS_CADENCE_CALENDAR.md](OPERATIONS_CADENCE_CALENDAR.md) に定義されています。

- **日次（Daily）**: Supabase/DBバックアップ確認、アップタイム監視アラート確認
- **週次（Weekly）**: コストダッシュボード確認、営業メール取り込みログ監視
- **月次（Monthly）**: 品質レポート生成、アクセスログ・監査ログのアーカイブ
- **四半期（Quarterly）**: セキュリティ監査、DR復旧訓練、依存ライブラリ更新
- **年次（Annual）**: シークレット鍵回転棚卸し、利用規約・プライバシーポリシー定期見直し

---

## 4. ドキュメント自動ガバナンスとCI品質ガード

ドキュメントの陳腐化やデッドリンクを防ぐため、CI環境（`python scripts/run_lane_preflight.py`）で以下の自動監査ガードが常時実行されます。

1. **ドキュメント参照整合ガード (`scripts/audit_docs_reference_integrity.py`)**: `docs/` 内の全相対パス・リンク解決を検証
2. **ID参照整合ガード (`scripts/audit_doc_id_references.py`)**: 本文中のタスクID(T###)、課題ID(R##)、QA ID(QA-##)が正本TSVに存在するか検証
3. **Runbookカタログ整合ガード (`scripts/audit_runbook_catalog.py`)**: 新規Runbookのカタログ登録漏れを防止
4. **品質ガードカタログ整合ガード (`scripts/audit_guard_catalog.py`)**: 登録された全品質ガードの文書化漏れを防止
5. **日本語表記表記揺れガード (`scripts/audit_japanese_wording_consistency.py`)**: UI/UXおよびドキュメントの標準用語統一を自動検証

---

## 5. 引継ぎチェックリスト

引き継ぎ時には以下の項目を確認してください。

- [ ] `docs/OPERATIONS_RUNBOOK_CATALOG.md` の全リンクが正常に閲覧できること
- [ ] `docs/OPERATIONS_CADENCE_CALENDAR.md` に基づく初回運用担当者の割り当てが完了していること
- [ ] `python scripts/run_lane_preflight.py --full` が一切のエラーなく成功すること
- [ ] 新任担当者が `docs/SETUP_GUIDE.md` を参照してローカル環境を再現できること
- [ ] Google Workspace / GCP / Firebase / Supabase / Stripe のアクセス権限が移行されていること
