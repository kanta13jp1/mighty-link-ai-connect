# セキュリティ・ログ健全性自動スキャンガード仕様書 (SECURITY_LOG_INTEGRITY_GUARD.md)

- 関連WBS: `T931` (8. 本番運用・品質管理 / セキュリティ監視)
- 担当レーン: `Antigravity + Gemini`
- 検証スクリプト: [`scripts/audit_security_log_integrity.py`](../scripts/audit_security_log_integrity.py)
- テストファイル: [`tests/test_security_log_integrity_audit.py`](../tests/test_security_log_integrity_audit.py)

---

## 1. 目的と保護対象

本ガードは、システム内のログ、エラーハンドリング、およびデータ永続化層において、以下のセキュリティ基準とコンプライアンスが恒常的に維持されていることをCI上で自動検証します。

1. **機密情報の非漏洩**: APIキー、OAuthシークレット、DB接続URL、パスワード等がログやソースコード内に平文で露出していないこと。
2. **要配慮個人情報の非永続化**: 適性診断・モチベーション診断の生回答や精神状態スコアが、DBや永続ログに蓄積されない構造（[`src/aptitude_demo.py`](../src/aptitude_demo.py) のDB非import性など）を担保。
3. **適切な認証・認可エラーハンドリング**: 401 Unauthorized / 403 Forbidden のHTTP例外がAPI層で適切にハンドリングされていること。
4. **仮名化・匿名化の徹底**: ログおよび公開マッチング結果において、`talent_label` や仮名化識別子が用いられていること。
5. **DoS・不正アクセス防御**: レートリミッター（[`src/rate_limit.py`](../src/rate_limit.py)）が有効に機能していること。

---

## 2. 10仮説と検証基準

| 仮説 | 検証内容 | 合格基準 |
|---|---|---|
| **H1** | 主要モジュール実在性 | `app.py`, `aptitude_demo.py`, `supabase_client.py`, `sales_email_match.py` が実在 |
| **H2** | 構造的非永続性 | `aptitude_demo.py` がDB/永続化ライブラリをimportしていない |
| **H3** | 機密情報漏洩パターン | コードベース内に平文シークレット・トークン正規表現パターンが0件 |
| **H4** | 認証エラー処理 | `app.py` 内に 401/403 エラーハンドリングが存在 |
| **H5** | セキュリティRunbook | `docs/SECURITY_INCIDENT_RESPONSE_RUNBOOK.md` が実在 |
| **H6** | プライバシー設計書 | `docs/APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md` が実在 |
| **H7** | 仮名化・匿名化 | `pseudonym` / `talent_label` による匿名化処理が存在 |
| **H8** | ガード仕様書 | 本仕様書が実在 |
| **H9** | レートリミット | `src/rate_limit.py` の RateLimiter が実在 |
| **H10** | 全体健全性 | 全仮説がPASSし、ドリフトが0であること |

---

## 3. 手動実行方法

```powershell
python scripts/audit_security_log_integrity.py
```
