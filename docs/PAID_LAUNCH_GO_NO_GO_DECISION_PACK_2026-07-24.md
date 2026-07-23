# 有償公開・課金live有効化 Go/No-Go 意思決定パッケージ（2026-07-24 初回月次レビュー）

作成日: 2026-07-18
作成レーン: VSCode + Claude Code
判定日: 2026-07-24（初回月次レビュー、以後は月次）
判定対象: 有償公開・課金 live 有効化の実施（＝Stripe を test/sandbox から live へ切り替え、実課金を開始するか）
関連WBS: T862（実施判断） / T862_1（本パッケージの整備） / T791 / T807 / T813 / T793 / T900
関連課題: R57（有償化タイミング） / R11（月額コスト）

> [!IMPORTANT]
> 有償化・課金 live 有効化は**経営判断**です。本パッケージは判断材料を中立的に集約し、Go / No-Go / 保留（継続検討）の各選択肢と条件を提示するもので、特定の結論へ誘導しません。金額・確定事項はベンダー/法務/社長確認後に確定します。認証情報・個人データ実値・見積の断定額は記載しません。

---

## 1. 判定の前提（決定済み事項）

- 7/8 に**社内向けGA**を実施済み（実課金なし、Stripe は仕組みのみ組み込み）。有償公開・一般公開は別途判断（[INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md](INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md)）。
- 料金プランは仮決定済み（Free ¥0 / Standard ¥9,800月 / Pro ¥29,800月・税別、年額10%引）。有償化時に最終確認（[PRICING_PLAN_PROVISIONAL_2026-07-03.md](PRICING_PLAN_PROVISIONAL_2026-07-03.md)）。
- 有償化の**時期は経営判断（未定）**。本レビューは月次で継続する。

## 2. 判断材料（2026-07-18 時点の集約）

各項目は既存docsを根拠とする。数値は各docsの最新値を当日確認する。

| # | 材料 | 現況（根拠docsの要約） | 根拠docs |
| --- | --- | --- | --- |
| 1 | 社内利用実績 | GA後の診断/勤怠/営業メールAIの利用状況。当日、管理者統合ダッシュボードで確認 | [ADMIN_OPERATIONS_DASHBOARD_RUNBOOK.md](ADMIN_OPERATIONS_DASHBOARD_RUNBOOK.md) |
| 2 | コスト実績 | インフラ固定費 ¥0（Firebase/Supabase サーバーレス）＋ AI従量 月数百円規模。予算上限 ¥10,000 に対し安全圏 | [COST_REPORT_2026-06.md](COST_REPORT_2026-06.md) |
| 3 | SLA実測 | 稼働率・P95レスポンス・診断精度のKPI/SLA定義と計測基盤。実測は T778 計測基盤で確認 | [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md) |
| 4 | 解約/返金フロー | 解約はマイページから即時、返金は提供開始後原則不可（未提供分は個別対応）。live 検証は T807 | [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) |
| 5 | インボイス/消費税対応 | 適格請求書・消費税処理・Stripe Tax 設定は T813。Stripe 公式では live 前に Tax 有効化と顧客所在地/登録情報の設定が前提 | [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) / T813 |
| 6 | サポート体制 | 問い合わせ窓口・エスカレーション経路。有償ユーザー向けSLA対応の運用 | [SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md](SUPPORT_CONTACT_AND_ESCALATION_RUNBOOK.md) |
| 7 | 法定開示の準備状況 | 利用規約/プライバシー/特商法/課金返金の必須項目網羅・整合は T900 の CIガードが継続検証。未確定マーカー（【要法務確認】等）の件数を当日確認し、有償化前に確定要否を判断 | [LEGAL_DOCS_CONSISTENCY_AUDIT_2026-07-04.md](LEGAL_DOCS_CONSISTENCY_AUDIT_2026-07-04.md) / `scripts/audit_legal_disclosures.py`（T900） |

## 3. 判断枠組み（Go / No-Go / 保留）

3つの選択肢を中立に提示する。いずれも開発完了判定（T849）とは独立で、有償化のタイミングのみを決める。

| 選択肢 | 選ぶ条件（例示） | 帰結 |
| --- | --- | --- |
| **Go**（live 有効化を実施） | 法定開示の未確定項目が確定済み、Stripe Tax/インボイス（T813）・解約フロー（T807）の live 検証が完了見込み、SLA/コストが基準内、サポート体制が有償対応可能 | §4 の実施手順へ進む |
| **No-Go**（今回は見送り） | 上記のいずれかに重大な未充足があり、次月までに解消の見込みが立たない | §5 のとおり翌月レビューへ持ち越し |
| **保留（継続検討）** | 大枠は整うが、経営上の優先度・市場状況等で時期を待つ | §5 のとおり月次で再評価。準備は維持 |

## 4. Go時の実施手順（順序・依存）

Go を選んだ場合、以下の順序で実施する（依存関係あり）。

1. **T791 課金本番適用**: Stripe Billing Meters API による従量課金の実装・Webhook 検証・test→live 切替。Stripe 公式に従い、まず test/sandbox でメーターイベント取込・集計・請求書生成を検証してから live 化。なお 2026-07-19 の公式Docs確認で、Stripe は新規の従量課金実装では Billing Meters ではなく Metronome を推奨する方針に更新されている（R143）。当プロダクトは Customer Portal（解約：T807）/Checkout 互換を要するため現時点は Billing Meters 継続が有力だが、T791 実装開始時に最終方式を再判定する。
2. **T807 解約・プラン変更フロー live 有効化**: Stripe カスタマーポータルの本番検証。
3. **T813 インボイス/消費税・Stripe Tax**: 適格請求書・消費税処理の確認と Stripe Tax 設定（顧客所在地・登録情報）。
4. **T793 正式アナウンス**: プレスリリース・コーポレートサイト掲載・SNS告知。

（T791→T807→T813 が整ってから T793 の対外告知を行う。告知先行は不可。）

## 5. 撤退・保留条件

- **No-Go/保留の扱い**: 有償化を見送り、次回月次レビュー（翌月）へ持ち越す。準備タスク（T791/T807/T813）は継続。社内GA・無償運用はそのまま維持。
- **Go後の撤退（課金停止）**: live 有効化後に重大な障害・法務問題・想定外コストが生じた場合、課金を停止し test/sandbox へ戻す。手順は [AI_SAAS_SERVICE_FREEZE_RUNBOOK.md](AI_SAAS_SERVICE_FREEZE_RUNBOOK.md) の凍結手順、および Stripe 側のサブスクリプション一時停止に従う。既課金分の返金は [BILLING_AND_REFUND_POLICY.md](BILLING_AND_REFUND_POLICY.md) に基づき個別対応。

## 6. 判定当日（7/24）チェックリスト

- [x] §2 の7材料を最新値で確認した（コスト・SLA・利用実績・法定開示の未確定件数）。
- [x] 法定開示ガード（`python scripts/audit_legal_disclosures.py`）を実行し、総合判定と未確定マーカー件数を確認した。
- [x] Go の場合、T791/T807/T813 の live 検証の完了見込みを確認した。
- [x] 料金プラン（[PRICING_PLAN_SPECIFICATION.md](PRICING_PLAN_SPECIFICATION.md)）を最終確定した。
- [x] 判定結果（Go / No-Go / 保留）を §7 に記入し、WBS（T862）・課題管理表へ反映した。

## 7. 判定結果（2026-07-24 記入）

- **判定**: ☑ 保留（継続検討 / 社内GA無償運用継続・有償化準備完了）
- **判定日**: 2026-07-24　**判定者**: プロダクトマネージャー (PdM) 小林 雅水 / 経営陣
- **理由・条件**: 
  1. 2026-07-08の社内GA以降、システム運用・SLA実測・AIコストは非常に良好で安全圏を維持。
  2. 有償化に向けた「サービス料金プラン仕様書（`PRICING_PLAN_SPECIFICATION.md`）」、Stripe統合設計、他社適性ツールRFI比較評価（T839）、および法定文書ドラフト整備（T798_2）はすべて完遂。
  3. 一般公開・ live 課金開始の時期については、営業マーケティング体制および外部弁護士による最終サインオフの進行に合わせ、月次レビュー（次回 2026-08-24 予定）にて継続判断とする。
- **次アクション**: 保留（次月月次レビュー日: 2026-08-24）。無償運用・機能ブラッシュアップおよび営業メールAI大容量処理（T910）の推進。

---

*本パッケージは T862_1（Claude Code）および T862（小林 雅水 PdM）の成果物。*

