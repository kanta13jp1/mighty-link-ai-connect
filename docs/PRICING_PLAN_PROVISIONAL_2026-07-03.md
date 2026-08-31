# 料金プラン仮決定 2026-07-03（T804 CEO承認前ドラフト）

作成日: 2026-07-03
担当レーン: Claude Code
ステータス: **承認済み（2026-07-03 プロジェクトオーナー承認・当面の正）**
関連WBS: T860（仮決定） / T861（スコープ再定義） / T804（完了） / T862（有償化判断） / T791 / T807 / T813
関連課題/QA: R111 / R112 / QA-92 / QA-93

> 2026-07-03 追記: 本仮決定はプロジェクトオーナー承認により当面の正となった（T804 完了）。ただし当面は社内ユーザーのみが使用し、課金は Stripe test mode の仕組みのみで**実課金は発生しない**（[INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md](INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md)）。live 課金有効化と CEO の最終価格確認は有償公開判断（T862）時に実施する。以下の「CEO承認事項」は T862 時の確認項目として保持する。
関連docs: [STRIPE_BILLING_INTEGRATION_DESIGN.md](STRIPE_BILLING_INTEGRATION_DESIGN.md) / [TOKUSHOHO_NOTATION.md](TOKUSHOHO_NOTATION.md) / [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) / [COST_REPORT_2026-06.md](COST_REPORT_2026-06.md)

---

## 目的

T804「料金プラン・価格設定の決定（CEO承認）」が具体的な検討材料なしに CEO 承認待ちとなっており、T791（Stripe Billing Meters 実装）、T807（Customer Portal live 有効化）、T813（インボイス・Stripe Tax）をブロックしていた。本docsで料金体系・無料枠・課金単位を**仮決定**し、CEO は本表の承認または修正のみを行えばよい状態にする。

仮決定の効力は次のとおり。

- Stripe **test mode** での Products / Prices / Meters 作成、Webhook・Customer Portal の実装検証（T791/T807）は本仮決定に基づき先行してよい。
- **live mode 有効化・有償販売開始・特商法/課金規約への価格確定記載は、T804 CEO承認と T798 法務確定の完了後に限る。**
- CEO が価格を修正した場合は、test mode の Prices/Meters を作り直してから live へ進む（QA-92）。

## 仮決定プラン表

月額は税別。特商法表記・申込画面では税込（消費税10%）で表示する。

| 項目 | Free | Standard | Pro | Enterprise |
| --- | --- | --- | --- | --- |
| 月額 | ¥0 | ¥9,800（税込 ¥10,780） | ¥29,800（税込 ¥32,780） | 個別見積 |
| 年額 | — | 月額12か月分の10%引 | 月額12か月分の10%引 | 個別見積 |
| ユーザー数上限 | 3 | 30 | 100 | 101以上 |
| AI診断（analysis_run）月間込み回数 | 10 | 200 | 1,000 | 個別 |
| 営業メールAIマッチング（sales_email_match_run）月間込み回数 | 10 | 200 | 1,000 | 個別 |
| 込み超過時の従量単価（両メーター共通） | 超過不可（ブロック） | ¥50/回 | ¥30/回 | 個別 |
| 管理者エクスポート | 3回/月 | 無制限 | 無制限 | 無制限 |
| サポート | コミュニティ/FAQ | メール | 優先メール・SLA目標適用 | 個別 |

- 勤怠・同意管理・基本管理者機能は全プラン共通で提供する（課金メーター対象外）。
- SLA 目標値は [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md) に従う。
- 想定主要顧客は中小SES・人材サービス企業。初期はスモールスタートしやすい月1万円弱の Standard を主力とする。

## 課金単位（Billing Meters）の仮決定

T776 で設計した3メーター候補のうち、次を採用する。

| メーター | 扱い |
| --- | --- |
| `analysis_run` | **課金メーター**。込み回数超過分を従量課金 |
| `sales_email_match_run` | **課金メーター**。込み回数超過分を従量課金 |
| `admin_export_run` | **当面は計測のみ（課金しない）**。Free の回数制限にのみ使用 |

idempotency key・個人情報非送信・Webhook 冪等処理は T776 設計（[STRIPE_BILLING_INTEGRATION_DESIGN.md](STRIPE_BILLING_INTEGRATION_DESIGN.md)）のとおり。

## 課金・支払条件の仮決定

- 決済手段: Stripe（クレジットカード）。Enterprise のみ請求書払いを個別対応。
- 課金サイクル: 申込日に初回課金、以後自動更新（[BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) 第2条と整合）。
- プラン変更: アップグレード即時（プロレーション）、ダウングレード次回更新日から（同 第3条と整合）。
- 消費税: 標準税率10%。税込表示。Stripe Tax の設定と適格請求書発行事業者登録の要否確認は T813 で実施。

## 価格の根拠

1. **原価構造**: [COST_REPORT_2026-06.md](COST_REPORT_2026-06.md) 実測で固定インフラ費 ¥0（Firebase/Supabase サーバーレス）、AI 変動費は Gemini Flash 系で月数百円規模。AI診断1回あたりの変動費は1円未満であり、従量単価 ¥30〜50/回 は十分な粗利を確保しつつ、込み回数超過のヘビーユースを回収できる。
2. **損益分岐**: Standard 1契約（¥9,800/月）で現行の全運用コストを回収できる。価格はコスト積み上げではなく価値ベースで設定し、無料枠は「社内トライアル1チーム分」（3ユーザー・各10回/月）に制限して転換を促す。
3. **価格帯**: 中小SES・人材企業の稟議を通しやすい月1万円弱（Standard）を主力に、利用量の多い企業向けに Pro で従量単価を下げる標準的な B2B SaaS 段階制とする。

## CEO承認事項（T804）

CEO には次の6点の承認または修正を依頼する。期限は **2026-07-07（T833 Go/No-Go）**。

1. プラン構成（Free / Standard / Pro / Enterprise）と月額価格
2. 無料枠の範囲（3ユーザー・AI診断/マッチング各10回/月）
3. 年額割引率（10%）
4. 従量超過単価（Standard ¥50/回、Pro ¥30/回）
5. Enterprise の個別見積・請求書払い方針
6. 適格請求書発行事業者登録の要否（T813 と連動、経理確認含む）

承認・修正の結果は本docsを確定版に改訂し、[TOKUSHOHO_NOTATION.md](TOKUSHOHO_NOTATION.md) と [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) の【要確認】箇所へ転記したうえで、T791 live 適用へ進む。
