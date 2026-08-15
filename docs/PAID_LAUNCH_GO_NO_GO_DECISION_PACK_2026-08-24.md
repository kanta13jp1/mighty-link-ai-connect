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

## 1. 判定の前提（決定済み事項）

- 7/8 に**社内向けGA**を実施済み、7/24の初回判定で「8/24持ち越し」を決定（[PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md](PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md)）。
- 料金プラン仕様（Free ¥0 / Standard ¥9,800月 / Pro ¥29,800月・税別、年額10%引）は正式版を制定済み（[PRICING_PLAN_SPECIFICATION.md](PRICING_PLAN_SPECIFICATION.md)）。
- 8/5 社長定例において、8/24 判定時の Go クリア基準（1,000件/日マッチング精度80%以上、SLA 99.9%、法務確定）を合意済み（[CEO_MEETING_AGENDA_2026-08-05.md](meetings/CEO_MEETING_AGENDA_2026-08-05.md)）。

---

## 2. 判断材料（2026-08-15 時点の集約）

| # | 材料 | 現況（根拠docsの要約） | 根拠docs |
| --- | --- | --- | --- |
| 1 | 営業メール実稼働精度 | 1日1,000件（月間3万件）規模のPOP3自動取り込み・AIマッチングにおいて、**適合率80%以上を維持・検証完了** | [SALES_PROPOSAL_EFFECTIVENESS_SUMMARY.md](SALES_PROPOSAL_EFFECTIVENESS_SUMMARY.md) / `T910` |
| 2 | 成約時間削減効果 | 営業メール受信から適合エンジニア提案までの所要時間を従来の3〜4時間から3〜5分へ短縮（**成約時間 97% 削減**の実測値） | [GROWTH_STRATEGY_ROADMAP.md](GROWTH_STRATEGY_ROADMAP.md) |
| 3 | コスト・収支実績 | インフラ固定費 ¥0（Firebase/Supabase サーバーレス）＋ AI変動原価（月数百円規模）。Standard 1契約で単月黒字化する損益分岐を維持 | [PRICING_PLAN_SPECIFICATION.md](PRICING_PLAN_SPECIFICATION.md) |
| 4 | SLA・稼働実績 | P95レスポンスタイム 2.0秒以内、システム稼働率 99.9% 以上のSLA基準を達成 | [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md) |
| 5 | セキュリティ・認可 | 全画面Fail-Closed認証（T915/T913）およびRBACアクセス制御（T914）をインフラチームと監査合意済み | [INFRA_HEARING_AGENDA_2026-08-07.md](meetings/INFRA_HEARING_AGENDA_2026-08-07.md) |
| 6 | 法定開示の準備状況 | 利用規約/プライバシー/特商法の法定3文書について、T900 CIガードにより未確定マーカー0件・弁護士最終確定のサインオフを確認 | [LEGAL_DOCS_CONSISTENCY_AUDIT_2026-07-04.md](LEGAL_DOCS_CONSISTENCY_AUDIT_2026-07-04.md) / `scripts/audit_legal_disclosures.py` |
| 7 | 差別化機能（ミキワメAI） | Pro向け「ミキワメAI第1弾データ連携PoC」のアーキテクチャ設計およびプロトタイプデモを整備完了 | [MIKIWAME_AI_INTEGRATION_POC_DESIGN.md](MIKIWAME_AI_INTEGRATION_POC_DESIGN.md) |

---

## 3. 判断枠組み（Go / No-Go / 保留）

| 選択肢 | 選ぶ条件（例示） | 帰結 |
| --- | --- | --- |
| **Go**（live 有効化を実施） | 営業メール精度80%超・成約時間97%削減の実証完了、法務サインオフ完了、Stripe Tax/インボイス（T813）および解約（T807）のlive検証準備完了 | §4 の実施手順へ進む |
| **No-Go**（今回は見送り） | 重大なシステム不具合または外部依存の致命的ブロッカーが存在する | 翌月レビューへ持ち越し |
| **保留（継続検討）** | 営業体制や対外プロモーションスケジュールの都合により公開時期を調整する | 月次で再評価 |

---

## 4. Go時の実施手順（順序・依存）

1. **T791 課金本番適用**: Stripe Billing Meters API 従量課金設定の test → live 切替
2. **T807 解約・プラン変更フロー live 有効化**: Stripe カスタマーポータルの本番稼働
3. **T813 インボイス/消費税・Stripe Tax**: 適格請求書番号および税率自動計算の最終確認
4. **T793 正式アナウンス**: プレスリリース・LP事前予約フォームの公開・SNS告知

---

## 5. 判定当日（8/24）チェックリスト

- [ ] §2 の7材料（精度80%、SLA、コスト、法定文書サインオフ等）を最終確認
- [ ] 法定開示ガード（`python scripts/audit_legal_disclosures.py`）の PASS を確認
- [ ] 料金プラン整合ガード（`python scripts/audit_pricing_consistency.py`）の PASS を確認
- [ ] 判定結果（Go / No-Go / 保留）を記入し、WBS（T862）・課題管理表へ反映
