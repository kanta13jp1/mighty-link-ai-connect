# Stripe Billing Meters API Sandbox 検証監査 (T958 / T791)

- **総合判定**: ✅ PASS (ドリフト0)
- **対象メトリクス**: `['admin_export_run', 'analysis_run', 'sales_email_match_run']`

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :-- | :-- | :-- | :-- |
| H1 | Billing Meterイベントペイロードが仕様に準拠 | ✅ | Valid |
| H2 | 要配慮個人情報・生メールアドレスのメーター送信を完全遮断 | ✅ | PII payload properly rejected |
| H3 | 全3種の定義済み課金メーター (analysis/sales_email/admin) の正常生成 | ✅ | Events: ['admin_export_run', 'analysis_run', 'sales_email_match_run'] |
| H4 | 冪等性キー (identifier) の指定と重複防止構造 | ✅ | Idempotency key preserved |
| H5 | Stripe Webhook 署名検証 (HMAC-SHA256) が正常動作 | ✅ | Signature verified successfully |
| H6 | 不正署名 Webhook リクエストを安全に拒絶 | ✅ | Invalid signature rejected |
| H7 | リプレイ攻撃対策 (Timestamp Tolerance 超過リクエストの遮断) | ✅ | Timestamp outside tolerance window (600s > 300s) |
| H8 | Stripe Billing 統合設計書 (T776/T791) が実在し整合 | ✅ | STRIPE_BILLING_INTEGRATION_DESIGN.md |
| H9 | Stripe Sandboxes 隔離運用方針（本番キー非混入・テストモード分離） | ✅ | Live keys excluded; Sandbox isolation enforced |
| H10 | Stripe Billing Meters Sandbox 検証ハーネス総合判定 | ✅ | PASS (ドリフト0) |
