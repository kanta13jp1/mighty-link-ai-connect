# MightyLink AI Connect 経理・税務・コスト管理運用手順書 (Accounting & Tax Operations Runbook)

作成日: 2026-07-24  
担当: 経理担当 / 財務管理  
ステータス: 正式合意運用版  
関連WBS: T813 / T823 / T862 / T862_1 / T757 / T736 / T847 / T906  
関連ドキュメント: [PRICING_PLAN_SPECIFICATION.md](PRICING_PLAN_SPECIFICATION.md) / [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) / [PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md](PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md) / [SERVICE_EOL_DECOMMISSIONING_PLAN.md](SERVICE_EOL_DECOMMISSIONING_PLAN.md)

---

## 1. 概要と基本方針

本手順書は、「MightyLink AI Connect」のサービス運営における経理・財務・税務・コスト監査の標準運用フローおよび法的要件を定めた規定ドキュメントです。

---

## 2. 適格請求書（インボイス制度）・消費税処理方針（T813）

1. **適格請求書発行事業者登録番号（T番号）の管理**:
   - 当社（株式会社MightyLINK）の適格請求書発行事業者登録番号（T+13桁）を管理し、有償化（live課金開始）の経営決定（T862）にあわせて Stripe Tax および Stripe 発行の領収書・請求書テンプレートへ登録・掲載します。
2. **消費税計算と表示規則**:
   - プラン価格は税別表示を基本とし、購入手続き画面・特商法表記・発行領収書においては消費税10%を加算した税込合計金額（例: Standard月額 ¥9,800（税込 ¥10,780） / Pro月額 ¥29,800（税込 ¥32,780））および消費税額を明示します。
   - 税率計算および顧客所在地判定は Stripe Tax により自動処理します。

---

## 3. 月次コスト台帳監査と予算消化率アラート管理

1. **予算割り当て・監視対象**:
   - `data/cost_allocation_budgets.tsv` に基づき、Gemini API、Supabase DB、Firebase/GCP、GitHub Actions、Stripe Billing 等の月間予算（合計目安 ¥10,000 / $100）を監視します。
2. **閾値アラートと自動遮断機能**:
   - 予算消化率 **80%** 到達時: 週次コストダッシュボード（`scripts/generate_weekly_cost_dashboard.py`）により通知を発行し、経理・インフラ担当へ警告を行います。
   - 予算消化率 **100%** 到達時: 外部API利用監査スクリプト（`scripts/audit_external_api_usage.py`）により無償枠・超過自動遮断ガードを発動し、予期せぬAI従量費用の肥大化を防止します。
3. **月次締め・報告サイクル**:
   - 毎月末締めで `scripts/generate_monthly_quality_report.py` を実行し、月次実績レポート（`docs/MONTHLY_REPORT_*.md`）を作成して経営陣およびプロダクトマネージャーへ報告します。

---

## 4. 法人決済アカウント・領収書集中管理（T823連動）

1. **決済手段の一元化**:
   - Google Cloud/Firebase、Supabase、GitHub、Stripe、ドメイン管理（お名前.com等）の決済名義をすべて「株式会社MightyLINK」の法人アカウントおよび法人クレジットカードへ統合・紐付けます。
2. **領収書・請求書保管フロー**:
   - 各クラウド基盤およびSaaSから発行される月次領収書・明細PDFは、発行日即日に経理保管ストレージへ自動集約・保存し、仕訳データと紐付けて管理します。

---

## 5. 会計処理・売上計上基準・法的帳簿保存

1. **売上計上基準**:
   - 月額サブスクリプション売上は、Stripe の月次確定日（サービス提供開始日・更新日）に基づき実現主義/発生主義で計上します。
   - 年額一括プラン等の前受金が発生した場合は、月次で按分計上処理を行います。
2. **解約・返金対応処理**:
   - 原則として提供開始後の未利用期間返金は行いません（[BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) に準拠）。二重課金やシステム障害等による例外返金が発生した場合は、Stripe Dashboard 経由で返金処理を行い、経理帳簿に返金雑損失/売上取消として計上します。
3. **法定帳簿・決済データの保存義務**:
   - 法人税法およびインボイス制度に基づき、決済ログ・適格請求書・領収書データ・同意履歴は **7〜10年間** 安全に保管します。
   - サービス終了時（EOL: [SERVICE_EOL_DECOMMISSIONING_PLAN.md](SERVICE_EOL_DECOMMISSIONING_PLAN.md)）であっても、これら法的保存対象データは消去除外データとして保存期間満了まで保持します。

---

## 6. ドキュメント改訂履歴

- **2026-07-24**: 初版作成（経理担当 / Grill-Me インタビュー合意結果を反映）
