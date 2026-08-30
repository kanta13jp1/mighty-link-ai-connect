# 有償公開・課金live有効化 Go/No-Go 意思決定パッケージ（2026-08-24 第2回月次レビュー）

作成日: 2026-08-15
作成レーン: 企画戦略担当 (Antigravity) + VSCode Claude Code
判定日: 2026-08-24（第2回月次レビュー）
判定対象: 有償公開・課金 live 有効化の実施（＝Stripe を test/sandbox から live へ切り替え、一般有償受付を開始するか）
関連WBS: `T862`（実施判断） / `T791` / `T807` / `T813` / `T793` / `T900`
関連課題: R57（有償化タイミング） / R11（月額コスト）

> [!IMPORTANT]
> 有償化・課金 live 有効化は**経営判断**です。本パッケージは判断材料を中立的に集約し、Go / No-Go / 保留（継続検討）の各選択肢と条件を提示するもので、特定の結論へ誘導しません。金額・確定事項はベンダー/法務/社長確認後に確定します。認証情報・個人データ実値・見積の断定額は記載しません。

---

## 1. 判定の前提

- 7/8 に社内向けGAを実施し、7/24の初回判定では有償公開を保留して8/24へ持ち越した（[前回判定](PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md)）。
- 料金表の文書間ドリフトは `audit_pricing_consistency.py` で0件。ただし価格関連の未確定マーカー3件は残る。
- 8/5の資料はGo基準を提示しているが、会議実施記録と人間の決裁署名はWBS `T911` で未確認である。アジェンダだけを承認証跡として扱わない。
- 2026-08-19に現行Stripe公式Docsを再確認した。Stripe Billing MetersはMeter Eventsを使う従量課金手順を引き続き公開し、Customer PortalもSandboxとliveを分離している。MetronomeはStripe傘下として案内されているが、Metronomeへの移行必須ではない。`R143` はこの事実確認で解決し、Go後の `T791` 開始時にAPI versionとDashboard設定を再確認する。

公式根拠: [Usage-based billing](https://docs.stripe.com/billing/subscriptions/usage-based) / [Pay-as-you-go implementation](https://docs.stripe.com/billing/subscriptions/usage-based/implementation-guide) / [Customer Portal](https://docs.stripe.com/customer-management/integrate-customer-portal)

---

## 2. 判断材料（2026-08-19 再監査）

| # | 材料 | 確認できた事実 | 未完了・制約 | 根拠 |
| --- | --- | --- | --- |
| 1 | 営業メール取込 | 最新成果物は `input_count=702`、案件378件、人材297件、タグ531件 | `model_name=deterministic-sales-email-extractor-v1`、`fallback_used=true`。1日1,000件のスループット試験ではない | `exports/sales_email_extraction_review.json` / `T910` |
| 2 | マッチング精度・時間削減 | 取込・構造化・画面表示の機能は実装済み | ラベル付き正解データによるprecision/recallと、作業時間のbefore/after計測がなく、精度80%・97%削減は未検証 | [営業効果サマリー](SALES_PROPOSAL_EFFECTIVENESS_SUMMARY.md) |
| 3 | コスト・収支 | 予算上限と監視ロジックは整備済み | `weekly_cost_dashboard.json` は `actuals=not configured`、`overall_status=unknown`。実請求データ未接続のため固定費0・黒字化を実績とは判定できない | `exports/weekly_cost_dashboard.json` |
| 4 | SLA・稼働 | 2026-08-04の単発監視は7/7対象が期待HTTP statusを返した | 月次KPIのavailability/P95/5xxはnullで、月間SLA実績は未計測。99.9%は目標値であり達成実績ではない | `exports/uptime_monitor_report.json` / `exports/monthly_quality_kpi_2026-06.json` |
| 5 | セキュリティ・認可 | 未認証トップ401、health 200、保護API401を2026-08-19のE2Eで再確認 | インフラ責任者のサインオフは未確認。提出パックの自己記載を承認証跡にしない | `T913`〜`T915` / `T845` / `T957` |
| 6 | 法定開示 | 必須項目と文書間整合はT900ガードでPASS | 未確定項目31件。法務・弁護士サインオフ未完了のため有償公開不可 | `scripts/audit_legal_disclosures.py` |
| 7 | 料金・差別化機能 | 料金整合ガードはPASS。ミキワメAI PoCの設計・ローカル実装は存在 | 料金未確定マーカー3件。ミキワメ外部APIとの本番契約・接続・DPAは別途確認 | `scripts/audit_pricing_consistency.py` / [PoC設計](MIKIWAME_AI_INTEGRATION_POC_DESIGN.md) |

---

## 3. 現時点の判定

**現時点の推奨判定: NO-GO（有償公開・Stripe live切替は実施しない）**

理由は、機能不全ではなく、外部向け実績として必要な測定と人間承認が未完了だからである。社内無償運用とSandbox準備は継続できる。

### Goへ変更できる条件

1. ラベル付き正解データで営業メール精度を評価し、母数・precision/recall・誤判定例を記録する。
2. 月間SLA実績とCloud/Firebase/Supabase/AIの実請求データを接続する。
3. 法定開示31件と料金3件の未確定項目を解消し、法務・経営の署名日を記録する。
4. `T845` 最終UAT、`T957` インフラサインオフ、`T911` 会議記録を人間が確定する。
5. 上記完了後に `T791` Sandbox実送信・Webhook・invoice previewを行い、live切替前に再判定する。

## 4. 判断枠組み（Go / No-Go / 保留）

| 選択肢 | 選ぶ条件（例示） | 帰結 |
| --- | --- | --- |
| **Go**（live 有効化を実施） | §3の5条件が証拠付きで完了し、CEOが日付入りで承認 | `T791` → `T807` → `T813` → `T793` |
| **No-Go**（今回は見送り） | 法務・SLA・コスト・精度のいずれかが未確認、または重大不具合が存在 | live課金と外部告知を停止し、解消タスクを継続 |
| **保留（継続検討）** | 技術・法務は完了したが、営業体制や公開時期の都合で延期 | 次回判定日と責任者を記録 |

---

## 5. Go時の実施手順（順序・依存）

1. **T791**: Stripe公式Docs/API versionを再確認し、SandboxでMeter Event、重複排除、Webhook、invoice previewを検証する。承認前にlive keyを使用しない。
2. **T807**: Customer PortalのSandbox設定で解約・プラン変更・支払方法更新を検証し、承認後にlive設定を分離作成する。
3. **T813**: 経理・法務が適格請求書、税率、事業者情報を確認し、Stripe Tax設定を証跡化する。
4. **T793**: 1〜3の完了後に限り、プレスリリース、コーポレートサイト、SNS告知を実施する。

---

## 6. 判定当日（8/24）チェックリスト

- [x] `python scripts/audit_paid_launch_evidence.py` がPASS（証拠整合性10/10検証完了）
- [x] 法定開示ガード（`python scripts/audit_legal_disclosures.py`）の PASS を確認
- [x] 料金プラン整合ガード（`python scripts/audit_pricing_consistency.py`）の PASS を確認
- [x] 法務31件・価格3件の未確定項目が有償公開を止める条件（保留理由）として記録されている
- [x] 精度・SLA・コストの実測証拠と、人間サインオフの要件定義を確認
- [x] 判定結果（保留 / 社内無償運用継続・Sandbox準備継続）と次回判定日（2026-09-24）をWBS・課題管理表へ反映

---

## 7. 8/24 確定判定記録

- **最終判定**: **保留（継続検討 / 社内GA無償運用継続・Sandbox準備完了）**
- **判定理由**: 社内GA運用および機能実装（マッチング、適性診断、認証保護）は高水準で稼働中であるが、外部有償公開に必須となる①実請求データ接続による黒字化実証、②法務・弁護士の確定サインオフ（未確定マーカー31件の解消）、③インフラ責任者サインオフが継続作業中であるため、安全第一のfail-closed原則に基づきlive切替を見送り、Sandbox検証および事前予約プロモーションを先行実施する。
- **次回月次レビュー予定日**: **2026-09-24**
- **T793処理**: 2026-08-30、保留判定に従ってプレスリリース・コーポレートサイト・SNSへの外部告知は実施せず、延期理由と次回判定日を記録して完了。

## 8. 2026-08-31 保留判定のタスク台帳への適用

全件CLOSE監査では、実施しないことが正式決定済みの有償公開工程を「未実装なのに完了」とは扱わず、**現在サイクルの延期判断が完了したタスク**として閉じる。

- `T791`: オフライン回帰10/10のみ。実Stripe Sandbox Meter/Event/Webhook/invoice previewは未実施。
- `T807`: Customer Portal Sandbox/live E2Eは未実施。live configurationは変更していない。
- `T813`: 経理・適格請求書・Sandbox請求書・Stripe Tax/liveは未実施。
- `T1002`: CEOの公開価格・有償化開始日は未承認。仮料金は社内無償運用の当面の正に限定する。
- `T1003`: 社内GA法務論点は確定済みだが、有償公開版の最終承認・版番号・適用日は未確定。

上記5件は2026-08-31付で延期CLOSEするが、Stripe Sandbox/live、公開価格、法務最終承認が完了したという証拠にはしない。`PUBLIC-04`は`HUMAN_GATE`、`PUBLIC-08`は`WARNING`、`PUBLIC-09`は`BLOCKED`を維持する。2026-09-24の次回レビューまたはそれ以前に有償公開検討を再開する場合、各工程を新しいWBS/Issueとして再起票し、最新のStripe公式仕様・会社承認・法務証跡で再評価する。
