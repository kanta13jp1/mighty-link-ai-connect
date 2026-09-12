# Stripe Customer Portal Runbook

更新日: 2026-07-01
対象WBS: T829（アプリ側セッションAPI・dry-run導線整備） / T776（課金統合設計） / T807（Stripe Dashboard live有効化・本番検証）

## ステータス

T829で、Stripe Customer Portalの短命セッションURLを作るアプリ側APIと、設定未完了でも検証できる `/billing` 画面を追加した。T776で課金本体、Webhook、Billing Meters、Sheets同期、Secret非記録の設計を [STRIPE_BILLING_INTEGRATION_DESIGN.md](STRIPE_BILLING_INTEGRATION_DESIGN.md) に切り出した。Stripe live key・Dashboard設定・テスト顧客でのend-to-end確認はT807で実施する。

現時点では一般公開・有償ローンチはNo-Goのまま。T804 価格決定、T791 Stripe課金本体、T807 Customer Portal live検証、T798 法務確認が残る。

## 公式Docs確認

2026-07-01に以下を確認した。

- Stripe Customer Portal integration: Customer Portalの設定、テスト、起動、webhook確認
- Stripe Billing Portal Sessions API: `POST /v1/billing_portal/sessions`、`customer`、`return_url`、`flow_data`、短命URL
- Stripe subscription cancellation: `cancel_at_period_end`、subscription updated/deleted event、請求期間末解約の考え方
- Stripe Webhooks: 署名検証、イベント再送、冪等処理

## 実装構成

| 項目 | 内容 |
|---|---|
| UI | `GET /billing` |
| API | `POST /api/billing/customer-portal/session` |
| Helper | `src/stripe_customer_portal.py` |
| テスト | `tests/test_stripe_customer_portal.py` |
| Rate limit | `/api/billing/customer-portal/session` を expensive API として制限 |

APIはFirebase Auth依存の `get_current_user` を通す。現行デモでは `MOCK_AUTH=1` が既定のためローカル確認は可能だが、本番ではFirebase Auth ID token必須運用にする。

## 環境変数

| 変数 | 必須 | 用途 |
|---|---:|---|
| `STRIPE_CUSTOMER_PORTAL_ENABLED=1` | live時必須 | Stripeへの外部通信を明示的に許可 |
| `STRIPE_SECRET_KEY` | live時必須 | Stripe API key。GitHub/Sheets/docsへ記録しない |
| `STRIPE_CUSTOMER_PORTAL_RETURN_URL` | 推奨 | Portal完了後の戻り先。未指定時は `https://mightylink-app.com/billing` |
| `STRIPE_CUSTOMER_PORTAL_CONFIGURATION_ID` | 任意 | Dashboardで作ったPortal configurationを固定する場合に使用 |

`STRIPE_CUSTOMER_PORTAL_ENABLED` または `STRIPE_SECRET_KEY` が無い場合、APIはStripeへ通信せず `status=preview` を返す。Customer IDとSubscription IDはpreviewでもマスクする。

## API契約

リクエスト例:

```json
{
  "customer_id": "cus_...",
  "return_url": "https://mightylink-app.com/billing",
  "flow_type": "subscription_cancel",
  "subscription_id": "sub_...",
  "dry_run": true
}
```

対応する `flow_type`:

- 空: Customer Portal home
- `subscription_cancel`: 解約導線。`subscription_id` 必須
- `subscription_update`: プラン変更導線。`subscription_id` 必須
- `payment_method_update`: 支払方法更新導線

live成功時はStripeの短命URLを `url` として返す。UIはこのURLを新規タブで開く。

## Stripe Dashboard手順（T807）

1. Test modeでCustomer Portal configurationを作成する。
2. 支払方法更新、請求書閲覧、プラン変更、解約を許可する。
3. 解約は課金規約第4条と合わせ、原則として現課金期間末で終了する設定にする。
4. Test customer / test subscriptionを作り、`/billing` から `dry_run=false` でセッション作成を確認する。
5. Portal上で解約・プラン変更・支払方法更新を実行し、Stripe DashboardのeventとWebhook受信ログを確認する。
6. Live modeのconfiguration IDとrestricted keyを会社管理Secretへ登録する。
7. SheetsのWBS、課題管理表、QA表へテスト結果を同期する。

## セキュリティ

- `STRIPE_SECRET_KEY` は環境変数またはGitHub Actions secretだけで扱う。
- Customer ID、Subscription ID、session URLをdocs、Issue、Sheets、NotebookLMへそのまま貼らない。
- Webhook raw payload、Stripe secret、署名ヘッダ、Customer Portal session URLをSheetsやdocsへ同期しない。
- `return_url` は `http` / `https` のみ許可する。
- Stripe API失敗時のエラーにはsecretを含めない。
- live通信は `STRIPE_CUSTOMER_PORTAL_ENABLED=1` が無い限り実行しない。

## 法務・ユーザー表示との整合

`docs/BILLING_AND_REFUND_POLICY.md` 第3〜4条、`docs/TOKUSHOHO_NOTATION.md` の解約方法欄と整合させる。

- 解約はアカウント設定またはCustomer Portalからいつでも可能。
- 解約後も現課金期間末まで利用可能。
- 期間途中の利用者都合解約では日割り返金しない。
- 返金はサポート経由で個別審査し、Stripe Refunds APIで元の支払方法へ返金する。

## 検証

T829で実施済み:

```powershell
pytest -q tests/test_stripe_customer_portal.py
```

T807で追加実施:

```powershell
pytest -q tests/test_stripe_customer_portal.py tests/test_api.py
python scripts/verify_public_demo.py --url https://mightylink-app.com/
```

Stripe test modeでは、Portal session作成、解約、プラン変更、支払方法更新、Webhook event、課金規約文言の整合を確認する。
