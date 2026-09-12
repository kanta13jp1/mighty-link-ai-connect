# 8/7(金) インフラチームヒアリング・懇親会 確認アジェンダ

作成日: 2026-07-24
対象: インフラチーム（杉村氏 ほか）、寛太梅澤、開発チーム
担当レーン: 企画戦略担当 (Antigravity) + Claude Code
関連WBS: [T878](../../data/WBS.tsv#L314)（インフラチームヒアリング・懇親会） / [T913](../../data/WBS.tsv#L351) / [T914](../../data/WBS.tsv#L352) / [T915](../../data/WBS.tsv#L353) / [T870](../../data/WBS.tsv#L303)
関連docs: [DEMO_SECURITY_AND_AUTH_DESIGN.md](../DEMO_SECURITY_AND_AUTH_DESIGN.md) / [FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md](../FIREBASE_AUTH_SUPABASE_RLS_SECURITY_DESIGN.md) / [SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md](../SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md)

---

## 1. ヒアリングの目的

本ヒアリングは、2026年8月7日(金)午後に実施されるインフラチームとの技術協議および同日夕方の懇親会に向け、本番セキュリティアーキテクチャの検証、システム安定性の確認、および運用監査サインオフを取得することを目的とします。

---

## 2. 最優先議題: セキュリティ＆認証運用監査サインオフ

### 【主題】Firebase Auth + FastAPI Fail-Closed 認証ガード（T913 / T914 / T915）
直近（7/23-7/24）で実施した全画面セキュリティ認証および静的バイパス遮断構成について、インフラチーム視点からの監査レビューと運用承認（サインオフ）を得ます。

1. **Firebase Hosting 静的配信バイパスの完全解消（T915）**:
   - `firebase.json` の rewrite 構成により、全リクエストを FastAPI へルーティング。
   - `firebase-hosting` 公開ディレクトリを空にし、未認証 DOM 露出を物理遮断した点の評価。
2. **FastAPI 認証ゲートの Fail-Closed 設計（T915）**:
   - 環境変数が未設定の場合、管理ランタイムが `503 Service Unavailable` を返し、静的フォールバックや未認証アクセスをシャットアウトする構造の確認。
3. **RBAC アクセスマトリックス（T914）と未ログイン時ロックアウト（T913）**:
   - anonymous / authenticated_user / admin / system_service の 4 ロール権限のインフラ整合性。

---

## 3. その他の協議事項

### 3-1. 営業メール POP3 自動受信用パイプラインの安定性（T910）
- お名前.com 転送 ＋ 自社 Google アカウント ＋ POP3 自動受信用スクリプト（1日1,000件規模）のネットワーク帯域および受入ソケットの監視。
- レート制限および IP ブロック回避のためのコネクション管理方針。

### 3-2. GCS バックアップ CI / DB 復旧パイプライン（T870 / R116）
- Workload Identity Federation (WIF) 再構成後の Supabase Daily Backup CI 実行状況。
- GCS private バケット管理および鍵ローテーション運用のインフラチームへの引き継ぎ確認。

---

## 4. 当日タイムスケジュール（8/7 金）

- **15:00 - 16:30**: インフラチーム技術ヒアリング・セキュリティ監査レビュー（会議室 / Google Meet）
- **16:30 - 17:00**: 運用サインオフ確認・質疑応答
- **18:00 - 20:00**: 懇親会（杉村氏ら参加）

---

## 5. サインオフ確認欄

- [ ] **セキュリティ・認証アーキテクチャ (T915/T913)**: インフラ運用承認取得
- [ ] **営業メール POP3 受信パイプライン (T910)**: ネットワーク安定性承認
- [ ] **バックアップ CI パイプライン (T870)**: 運用引き継ぎ確認完了
