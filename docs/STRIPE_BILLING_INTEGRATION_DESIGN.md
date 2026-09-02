# Stripe Billing 統合設計（T776）

更新日: 2026-07-01
対象WBS: T776（完了） / T791（Billing Meters・Webhook実装） / T807（Customer Portal live検証） / T813（税・請求書）
担当レーン: Codex

## ステータス

T776では、Mighty-Link AI Connect の有料プラン課金フロー、Stripe Billing Meters、Webhook、領収書・請求書、Google Sheets同期、Supabase保存境界を設計した。

この設計完了は **public_paid_launch の許可ではない**。一般公開・有償ローンチは、少なくとも T791、T807、T804、T798、T770、T752、T845、T849、T852、T855 の各ゲート完了後に再判定する。

## 公式ドキュメント確認

2026-07-01に、T776へ直接関係する次の公式ドキュメントを確認した。

- Stripe Billing: https://docs.stripe.com/billing
- Stripe Subscriptions: https://docs.stripe.com/billing/subscriptions/overview
- Stripe Webhooks: https://docs.stripe.com/webhooks
- Stripe Customer Portal: https://docs.stripe.com/customer-management
- Stripe Invoicing: https://docs.stripe.com/invoicing
- Stripe Tax: https://docs.stripe.com/tax
- Firebase Functions / Hosting: https://firebase.google.com/docs/functions / https://firebase.google.com/docs/hosting
- Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions: https://docs.github.com/actions

API versionは実装開始時点でStripe Dashboardと公式ドキュメントを再確認し、T791のコード・Runbookで明示的に固定する。過去メモのAPI version文字列を根拠に実装しない。

## 採用方針

| 領域 | 方針 |
| --- | --- |
| 決済・カード保存 | Stripeに委任し、カード番号はアプリ、Supabase、Sheets、GitHub、docsへ保存しない |
| 初回申込 | Stripe CheckoutまたはCheckout相当のStripe-hosted導線を使う。申込前に同意UIと特商法6項目を表示する |
| サブスクリプション | Stripe Subscriptionを課金状態の正本とし、アプリDBは参照用スナップショットだけを保持する |
| 従量課金 | Stripe Billing Metersへmeter eventを送信する。アプリ側は送信前後の最小メタデータを台帳化する |
| 解約・プラン変更 | T829のCustomer Portal session APIを使い、T807でDashboard test/live設定とE2E確認を行う |
| 領収書・請求書 | Stripe hosted invoice / receiptを正本にする。税・適格請求書・消費税設定はT813で確認する |
| Google Sheets同期 | raw payloadではなく、イベント種別、集計件数、処理状態、マスク済みIDだけを同期する |

## エンドツーエンド課金フロー

1. ユーザーが有料プランを選ぶ。
2. 申込前UIで、利用規約、プライバシーポリシー、特商法表記、課金規約、価格、自動更新、解約条件を確認する。
3. アプリはFirebase AuthのUIDとテナント情報を確認し、既存Stripe Customerがあれば再利用する。
4. Stripe Checkout sessionを作成し、success/cancel URLを返す。
5. Checkout完了後、アプリ画面は即時に「受付中」と表示し、課金状態の正本更新はWebhookを待つ。
6. `checkout.session.completed`、`customer.subscription.created`、`customer.subscription.updated`、`invoice.paid` などのWebhookでSupabaseのスナップショットを更新する。
7. `invoice.payment_failed`、`customer.subscription.deleted`、`customer.subscription.updated` の状態に応じて、猶予期間、機能制限、解約済み表示を反映する。

## 使用量課金設計

Mighty-Link AI Connectで課金対象にし得る利用量は、T804の価格承認後に確定する。T776時点では次の候補を想定する。

| メーター候補 | 説明 | meter eventのキー方針 |
| --- | --- | --- |
| `analysis_run` | 履歴書・案件解析の実行回数 | Firebase UIDやメールを直接送らず、アプリ内の疑似IDと処理IDを使う |
| `sales_email_match_run` | 営業メールAIマッチング実行回数 | メール本文、送信者名、案件本文は送らない |
| `admin_export_run` | 管理者CSV/レポート出力回数 | 出力ファイル名や個人識別子は送らない |

meter event送信は、二重課金を避けるためアプリ側でidempotency keyを生成する。キーは `tenant_id`、課金対象日、機能種別、内部イベントIDから作り、個人情報を含めない。

## Webhook設計

Webhook endpointはT791で実装する。必須ルールは次のとおり。

- Stripe signatureを検証し、未検証payloadは処理しない。
- `event.id` を一意キーとして保存し、同じWebhookの再送を冪等に処理する。
- 2xx応答は保存・キュー投入が完了した後に返す。下流処理失敗時は再試行可能にする。
- raw payloadはGitHub、Sheets、docs、NotebookLM、Slack、Issueへ保存しない。
- Supabaseに保存するWebhook記録は、`event_id`、`event_type`、`livemode`、`created_at`、処理状態、関連オブジェクトIDのマスク値、エラー分類に限定する。
- secret、署名ヘッダ、カード情報、メールアドレス、住所、請求先氏名はログから除外またはredactする。

T791で最低限処理するイベント:

| イベント | 目的 |
| --- | --- |
| `checkout.session.completed` | 初回申込受付、Customer/Subscription紐付け |
| `customer.subscription.created` | subscriptionスナップショット作成 |
| `customer.subscription.updated` | プラン変更、cancel_at_period_end、支払い状態更新 |
| `customer.subscription.deleted` | 解約・終了反映 |
| `invoice.paid` | 支払い成功、領収書・請求書URLのマスク済み参照 |
| `invoice.payment_failed` | 支払失敗、dunning・機能制限候補 |

## Supabaseスキーマ案

T791では次のテーブルを追加または実装候補にする。RLSは必須で、service role以外の不要な直接アクセスはREVOKEする。

| テーブル | 用途 | 保存禁止 |
| --- | --- | --- |
| `billing_customers` | app user/tenantとStripe Customerのマスク済み対応 | raw customer IDの公開、カード情報 |
| `billing_subscriptions` | subscription状態スナップショット | 請求先住所・氏名・カード情報 |
| `billing_usage_events` | meter event送信台帳 | メール本文、履歴書本文、個人名、API key |
| `stripe_webhook_events` | Webhook冪等処理と監査 | raw payload、署名secret |
| `billing_invoice_snapshots` | invoice状態とhosted invoice参照 | PDF原本、カード番号 |

実Stripe IDを保持する必要がある場合は、SupabaseのRLS、管理者専用API、ログredactionを前提にし、Sheets・Issue・docsでは必ずマスクする。

## 環境変数・Secret

| 変数 | 用途 |
| --- | --- |
| `STRIPE_SECRET_KEY` | Stripe API実行。GitHub Actions secretまたは会社指定Secret管理のみ |
| `STRIPE_WEBHOOK_SECRET` | Webhook署名検証。成果物へ記録しない |
| `STRIPE_PRICE_*` | T804で承認されたPrice ID。docsでは実値をマスクする |
| `STRIPE_BILLING_METER_*` | T791で作成したMeter ID。Sheets/docsでは実値をマスクする |
| `STRIPE_CUSTOMER_PORTAL_ENABLED` | Customer Portal live通信許可 |

## Sheets同期設計

Sheetsへ同期してよい情報:

- 日別のWebhook受信件数
- イベント種別ごとの成功・失敗・再試行件数
- マスク済みCustomer/Subscription/Invoice ID
- テストモードかlive modeか
- T791/T807の検証結果、スクリーンショットではなく手順結果と判定

Sheetsへ同期しない情報:

- Webhook raw payload
- Stripe secret key、webhook secret、署名ヘッダ
- カード番号、有効期限、CVC、支払方法詳細
- 請求先氏名、住所、メールアドレスの実値
- Customer Portal session URL

## T791受け入れ条件

T791を完了にできる条件:

1. Stripe Checkoutまたは申込導線が同意UI・特商法6項目・T804価格と整合している。
2. Billing Metersへテストmeter eventを冪等に送信できる。
3. Webhook署名検証、冪等処理、最小保存、失敗再試行がテストされている。
4. Supabase RLS/REVOKEが適用され、raw payloadやsecretが保存されないことをpytestで確認している。
5. 領収書・請求書はStripe hostedの参照に限定し、T813未完了の税要件を勝手に確定しない。
6. Sheets同期はマスク済み集計だけで、raw payloadや実IDを含まない。
7. `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` がPASSする。

## T807受け入れ条件

T807を完了にできる条件:

1. Stripe Dashboard test modeでCustomer Portal configurationを確認する。
2. 解約、プラン変更、支払方法更新、請求書閲覧をテスト顧客でE2E確認する。
3. Webhook eventとアプリ側状態が一致する。
4. live modeのSecretとconfigurationを会社管理Secretへ登録し、実値を成果物へ記録しない。
5. `docs/STRIPE_CUSTOMER_PORTAL_RUNBOOK.md` と `docs/BILLING_AND_REFUND_POLICY.md` の記述が一致している。

## 残ゲート

| WBS | 残内容 |
| --- | --- |
| T791 | Stripe Billing Meters、Webhook、課金本体の実装・検証 |
| T807 | Customer Portal live有効化・本番検証 |
| T813 | 消費税、請求書、税務・領収書要件の確認 |
| T804 | 料金プラン・価格のCEO承認 |
| T798 | 利用規約・プライバシー・課金規約・特商法の法務確認 |
| T752 | ユーザー別オンボーディング・同意履歴・アカウント有効化 |
| T845/T849 | 全機能UATとサイト開発完了総合判定 |

## 関連ドキュメント

- [課金規約・返金ポリシー](BILLING_AND_REFUND_POLICY.md)
- [特定商取引法に基づく表記](TOKUSHOHO_NOTATION.md)
- [Stripe Customer Portal Runbook](STRIPE_CUSTOMER_PORTAL_RUNBOOK.md)
- [Go/No-Goチェックリスト](PRODUCTION_GO_NO_GO_CHECKLIST.md)
- [AI/SaaSサービス凍結Runbook](AI_SAAS_SERVICE_FREEZE_RUNBOOK.md)
