# アーキテクチャ意思決定記録（ADR）

作成日: 2026-07-20 / 担当レーン: Claude Code（T912）
目的: 本プロジェクトの主要な技術・構成の意思決定を「なぜそう決めたか・何を却下したか・その結果どうなるか」まで残し、**会社への運用引継ぎ（T850）と開発完了判定（T849）で第三者が構成の理由を独力で追える**ようにする。

> [!NOTE]
> 各ADRの根拠は既存docs・課題管理表の**実記録**に紐づけている。推測や後付けの理由は記載しない。
> 決定を変更する場合は既存ADRを書き換えず、ステータスを「廃止」または「見直し中」に更新し、新しいADRを追記すること。
> 記録の完全性は `scripts/audit_architecture_decisions.py`（T912）が毎回検証する（要素欠落・代替案の空欄・根拠docsの切れリンクを検知）。

**ステータスの意味**: `採用済み` = 現構成として稼働中 / `見直し中` = 再評価が進行中 / `廃止` = 後継ADRに置き換え済み

---

## ADR-0001: ホスティングとデータベースに Firebase + Supabase のサーバーレス構成を採用する

- **背景**: 当初はホスティングに Render（月額約1,000円）を想定していたが、月額コスト上限（課題 R11 / 論点 Q-OPS-09 で合意した上限 ¥10,000）に対し、収益化前の段階で固定費を発生させることが妥当かが論点になった。
- **決定**: ホスティングを **Firebase（Hosting + Cloud Functions）**、データベースを **Supabase（マネージド PostgreSQL）** とするサーバーレス構成に確定する（社長の指示により確定）。
- **代替案と却下理由**:
  - **Render（当初案・月額約1,000円）** — 常時起動のインスタンス課金が発生する。収益化前に固定費を負う必要がないため却下。
  - **Firestore（Firebase 内で完結する NoSQL）** — 本プロダクトは適性診断・勤怠・営業メールマッチングで関係モデルと集計クエリを多用するため、リレーショナルDB（PostgreSQL）が適する。RLS による行レベル権限制御も要件に合致するため Supabase を採用。
- **影響**:
  - インフラ固定費が **月額 0円** になった（変動費は AI 従量のみ）。有償化判断（T862）のコスト材料もこれを前提とする。
  - サーバーレスのためコールドスタートと接続プール枯渇が新たな運用論点になり、[Supabase 接続プール運用](SUPABASE_CONNECTION_POOLING_RUNBOOK.md) と [パフォーマンス診断](PERFORMANCE_DIAGNOSTIC_AND_INDEX_OPTIMIZATION_RUNBOOK.md) が必要になった。
  - Postgres のメジャーバージョン EOL 追従が自前の責務になった（[Postgres アップグレード](SUPABASE_POSTGRES_UPGRADE_RUNBOOK.md)）。
- **ステータス**: 採用済み
- **根拠docs**: [ホスティング/DB選定報告書](HOSTING_AND_DATABASE_SELECTION.md) / [コストレポート 2026-06](archive/historical_reports/COST_REPORT_2026-06.md) / [Supabase インフラ監査](SUPABASE_INFRA_AUDIT_2026-07-04.md)

## ADR-0002: 本番ドメインは専用ドメインを新規取得し、レジストラに お名前.com を用いる

- **背景**: 本番公開（T740）にあたり販売URLのカスタムドメインが必要になった。当初は会社ドメイン `ml-mightylink.com` の利用を想定していたが、DNS レコードを追加できず作業がブロックされた。
- **決定**: 会社ドメインではなく **専用ドメイン `mightylink-app.com` を新規取得**し、レジストラを **お名前.com** として運用する。
- **代替案と却下理由**:
  - **会社ドメイン `ml-mightylink.com` のサブドメイン利用** — 課題 **R54** の調査で、`kanta13jp@gmail.com` の全12プロジェクト・`k-umezawa@ml-mightylink.com` の全3プロジェクトのいずれにも当該 Cloud DNS ゾーンが存在せず、**ゾーン所有アカウントを特定できなかった**ため CNAME を追加できない。公開期日を守れないため却下。
  - **GitHub Pages の既定ドメインのみで公開** — CEO 共有済みの公開デモURLとしては機能するが、販売URLとして独自ドメインの HTTPS 提供が必要なため、これ単独では不採用（デモ用途としては現在も併用）。
- **影響**:
  - ドメインの更新・DNS 管理責任が自プロジェクト側になり、**更新失効が停止リスク**になった。実際に 2026-06-27 に DNS/HTTPS の停止事象が発生している（[インシデント記録](archive/historical_reports/CUSTOM_DOMAIN_UPTIME_INCIDENT_2026-06-27.md)）。
  - 死活監視で `https://mightylink-app.com/` を厳格HTTPS監視の対象にした（[死活監視Runbook](UPTIME_MONITORING_AND_ALERT_RUNBOOK.md)）。
  - サービス終了時はドメインの自動更新停止時期を明示的に決める必要がある（[EOL計画](SERVICE_EOL_DECOMMISSIONING_PLAN.md) §7）。
- **ステータス**: 採用済み
- **根拠docs**: [本番ドメイン設定ガイド](PRODUCTION_DOMAIN_SETUP_GUIDE.md) / [カスタムドメイン停止インシデント](archive/historical_reports/CUSTOM_DOMAIN_UPTIME_INCIDENT_2026-06-27.md) / 課題管理表 `data/issues_tracker.tsv` の R54

## ADR-0003: AIモデルに Google Gemini（Flash 系）を主推論基盤として採用する

- **背景**: 経歴書パース・適性診断・営業メールマッチングで LLM 推論を多用するため、月額コスト上限（R11）内に収まる推論基盤を選ぶ必要があった。
- **決定**: 主モデルに **Gemini（Flash 系）** を採用し、モデル版は追従ポリシーで管理する。
- **代替案と却下理由**:
  - **高性能モデル（Pro 系・他社の上位モデル）の常用** — 実測で Flash 系の週次コストは約 $1.20（約180円）に収まり、無料枠または微小な従量課金で足りた。本プロダクトの推論はパースと定型スコアリングが中心で上位モデルの精度差が費用差に見合わないため、常用は却下（重い判断が必要な箇所のみ個別検討）。
  - **推論の自前ホスティング** — サーバーレス構成（ADR-0001）で固定費0を実現した方針と矛盾し、GPU 固定費が発生するため却下。
- **影響**:
  - AI が利用不可でも機能停止しないよう、**決定論的フォールバック**（`AI_FORCE_MOCK=1`）を実装した。ただし利用者に「サンプル値」と明示する透明性が必須になった（`scripts/audit_diagnosis_fallback_transparency.py`）。
  - モデル版の非推奨・EOL 追従が定期運用義務になった（[Geminiモデル追従Runbook](GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md)、年次確認は[運用カレンダー](OPERATIONS_CADENCE_CALENDAR.md)）。版ポリシー適合は `scripts/audit_gemini_model_policy.py` が検証する。
- **ステータス**: 採用済み
- **根拠docs**: [コストレポート 2026-06](archive/historical_reports/COST_REPORT_2026-06.md) / [Geminiモデル追従・移行Runbook](GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md)

## ADR-0004: 課金基盤に Stripe を採用し、live 有効化は経営判断まで行わない

- **背景**: 有償化に備えて課金・サブスクリプション基盤が必要だが、社内利用フェーズでは実課金が発生しない。実装をどこまで先行させるかを決める必要があった。
- **決定**: 課金基盤に **Stripe** を採用する。実装・検証は **Sandbox / test mode に限定**し、**live 有効化と実課金の開始は経営判断（T862）の後**に行う。
- **代替案と却下理由**:
  - **live を先に有効化して実課金で検証する** — 法定開示（特商法・返品/解約）と適格請求書（インボイス）対応が未確定のまま実課金を開始すると法務リスクがあるため却下。有償公開前必須の論点は法務確認台帳で管理する。
  - **自前課金実装** — 決済情報の保持責任（PCI DSS 相当）を自プロジェクトで負うことになり、規模に見合わないため却下。
- **影響**:
  - 解約・プラン変更は Stripe カスタマーポータルに委ねる設計になった（[Stripe Customer Portal Runbook](STRIPE_CUSTOMER_PORTAL_RUNBOOK.md)、live 検証は T807）。
  - 料金プランは仮決定として複数docsに引用されるため、価格ドリフト検知ガードが必要になった（`scripts/audit_pricing_consistency.py`・T901）。
  - 2026-07-19 の公式Docs確認で、Stripe が新規の従量課金実装で Billing Meters ではなく Metronome を推奨する方針に更新されていることを検出（課題 **R143**）。当プロダクトは Customer Portal / Checkout 互換を要するため現時点は Billing Meters 継続が有力で、最終方式は T791 実装開始時に再判定する。
- **ステータス**: 見直し中（採用は確定。従量課金の実装方式のみ R143 で再判定予定）
- **根拠docs**: [Stripe課金統合設計](STRIPE_BILLING_INTEGRATION_DESIGN.md) / [課金・返金ポリシー](BILLING_AND_REFUND_POLICY.md) / [有償公開 Go/No-Go 意思決定パッケージ](PAID_LAUNCH_GO_NO_GO_DECISION_PACK_2026-07-24.md)

## ADR-0005: 開発を 3 レーン（Antigravity+Gemini / Codex / Claude Code）並走体制で進める

- **背景**: 単一 AI ツールでの開発は、ツール側のクォータ制限で作業が止まるリスクと、実装・レビューが同一主体になり第三者検証が働かない問題があった。
- **決定**: **Antigravity + Gemini**（フロントエンド・マルチモーダル）、**Codex**（バックエンド・同期スクリプト・CI）、**Claude Code**（ドキュメント・レビュー・品質ガード・調停）の 3 レーン並走体制を採る。
- **代替案と却下理由**:
  - **単一ツールでの開発** — Gemini のクォータ上限に達した時点で開発が停止する（実際に発生し、Codex への切り替え手順を整備した）。また実装者と検証者が同一になり、第三者レビューが働かないため却下。
  - **レーンごとにリポジトリを分離する** — 正本（WBS・課題/QA表）が分散し整合が取れなくなるため却下。単一リポジトリ・単一 main を共有し、コミットをレーン別に分ける運用とした。
- **影響**:
  - 同一ワーキングツリーを複数レーンが同時編集するため、**コミット前の `git status` 再確認とレーン別コミット**が必須運用になった。他レーンの未コミット作業を巻き込まない/破棄しない分離手順を運用ルール化している。
  - コミット前の共通検証として、全整合ガードと全テストを 1 コマンドで実行する[レーン・プリフライト](LANE_PREFLIGHT_GUARD.md)（T894）を導入した。
  - レーン間の第三者レビュー（あるレーンの成果物を別レーンが検証する）が品質改善に機能している。
- **ステータス**: 採用済み
- **根拠docs**: [マルチAI開発ワークフロー](MULTI_AI_WORKFLOW.md) / [レーン・プリフライトガード](LANE_PREFLIGHT_GUARD.md) / [Codex継続作業メモ](CODEX_CONTINUATION_NOTES.md)

---

*本記録は T912（Claude Code）の成果物。新しい主要決定を行ったら本ファイルへ ADR を追記すること（要素欠落や代替案の空欄はCIガードが検知して失敗する）。*
