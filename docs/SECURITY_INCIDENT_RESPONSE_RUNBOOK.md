# セキュリティインシデント対応・ログ健全性運用Runbook

作成日: 2026-08-15  
担当: セキュリティ担当 (山田 太郎) + 企画戦略担当 (Antigravity)  
対象: 全システム運用者・開発者  
関連WBS: `T931` / `T913` / `T914` / `T915`  
関連docs: [APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md](APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md) / [DEMO_SECURITY_AND_AUTH_DESIGN.md](DEMO_SECURITY_AND_AUTH_DESIGN.md) / [SECURITY_LOG_INTEGRITY_GUARD.md](SECURITY_LOG_INTEGRITY_GUARD.md)

---

## 1. 概要

本Runbookは、不正アクセス、認証・認可違反、機密情報漏洩兆候、および要配慮個人情報の不正蓄積が発生した際、迅速な検知・隔離・封じ込め・原因分析を行うための手順書です。

---

## 2. ログ健全性基準と禁止事項

1. **機密情報のログ出力禁止**:
   - APIキー（Gemini / Stripe / Supabase）、OAuthトークン、パスワードをログ・DBへ平文出力することを厳禁。
2. **要配慮個人情報の非保存原則**:
   - 社員適性診断・モチベーション診断の生スコアや回答をDB/ログへ永続化せず、セッション内でのみ揮発的に処理。
3. **監査ログの記録必須項目**:
   - 認証失敗（401）、認可拒否（403）、および異常なリクエスト頻度（429）を監査ログ（JSONL）へタイムスタンプ付きで記録。

---

## 3. インシデント発生時の緊急エスカレーションフロー

1. **フェーズ 1 (初動対応・隔離)**:
   - 攻撃元IPの即時遮断（FastAPI レートリミット / Cloud Armor / WAF）。
   - 必要に応じて `FAIL_CLOSED=true` で認証ゲートをシャットアウト。
2. **フェーズ 2 (証跡保全と分析)**:
   - 監査ログの退避・ハッシュ値検証。
   - `python scripts/audit_security_log_integrity.py` を実行し、システム全体の健全性を再スキャン。
3. **フェーズ 3 (復旧と再発防止)**:
   - 影響範囲の特定、APIキーのローテーション、および関係者への報告。
