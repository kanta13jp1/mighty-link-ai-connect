# AI 開発ツール月額サブスクリプション & クォータポリシー (T932)

本ドキュメントは、Mighty Skill-Bridge プロジェクトにおける 3 大 AI 開発基盤モデルおよびツールの月額枠・用途・利用上限ポリシーを規定します。

---

## 1. 3大 AI 開発ツールの利用方針と予算配分

| ツール / プロバイダ | 主な用途・担当領域 | 月額予算 / 利用枠 | サーキットブレーカー / 上限設定 |
| :--- | :--- | :--- | :--- |
| **Google Gemini (Gemini 2.5/3.1)** | コアバックエンド AI パイプライン (営業メール抽出・適合マッチング) | API 従量課金 ($50/月 予算上限) | 日次 100,000 トークン上限・超過時決定論的フォールバック |
| **Anthropic Claude (Claude Code)** | ドキュメント監査・コードレビュー・ADR策定・仕様書整合性検証 | サブスクリプション枠 ($40/月) | セッションあたりのトークン自動制限 |
| **OpenAI Codex / GPT** | バックエンド・データ同期・自動化スクリプト開発・リファクタリング | API / ツール枠 ($40/月) | 日次 API 呼出上限設定 |

---

## 2. 課金爆発防止（Billing Safety & Circuit Breaker）

1. **サーキットブレーカーの自動遮断**:
   - `src/app.py` において、1日のトークン消費または呼び出し回数が上限に達した場合、自動的に外部 API 呼び出しを遮断し、インプロセス・ルールベース処理へフォールバックします。
2. **管理ダッシュボードでの可視化**:
   - `admin/index.html` および `/api/admin/usage` エンドポイントにより、当日の消費トークン数・API呼び出し回数をリアルタイム監視します。
3. **緊急停止 Runbook**:
   - 異常なクォータ超過検知時は [AI_SAAS_SERVICE_FREEZE_RUNBOOK.md](AI_SAAS_SERVICE_FREEZE_RUNBOOK.md) の手順に従い即座に該当プロバイダを緊急停止（Freeze）します。

---

- [Master Knowledge Graph Index](MASTER_KNOWLEDGE_GRAPH.md)
- [Cost Quota Alerts Guard](COST_QUOTA_ALERTS_GUARD.md)
