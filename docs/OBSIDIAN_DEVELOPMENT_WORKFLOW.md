# Obsidianを活用したローカル開発プロセスガイド

作成日: 2026-08-05  
関連WBS: T929 / T628  
担当: Antigravity + Gemini / Codex / Claude Code  

---

## 1. 目的と基本思想

本ドキュメントは、Mighty Link AI Connect プロジェクトにおいて、ナレッジ管理ツール **Obsidian** を開発フローへ統合し、個人/チームのローカル思考・実験プロセスを高速化しつつ、公式情報ソース（[data/WBS.tsv](../data/WBS.tsv) および [docs/](./)）とのガバナンスを保つための運用ガイドラインです。

### 1.1 基本原則 (Separation of Concerns)

1. **公式情報の絶対性 (Source of Truth)**:
   - Git リポジトリ配下の `data/WBS.tsv`, `data/issues_tracker.tsv`, `docs/*.md` が確定仕様・公式記録の正本です。
   - Obsidian 内のメモはデフォルトで「未確定アイデア・ローカル実験場」として扱います。
2. **プレーンテキスト & ローカルファースト**:
   - Obsidian は標準 Markdown を採用するため、ベンダーロックインなくローカルファイルシステム上で高速かつオフラインで動作します。
3. **双方向リンク (WikiLinks) によるナレッジグラフ可視化**:
   - 単発のメモに終わらせず、`[[T929]]`, `[[R148]]`, `[[ADR-0005]]` などの参照リンク（WikiLinks）を張ることで、タスク・課題・設計判断の相関関係を可視化します。

---

## 2. Obsidian 開発プロセスの 4 層構造 (4-Tier Knowledge Architecture)

```
[ Tier 1: キャプチャ & スクラッチ ]
   │  00_Inbox / デイリーノート / 30_Meetings 素案
   ▼
[ Tier 2: アーキテクチャ & プロンプトラボ ]
   │  10_ADR_Drafts / 20_Prompts / 40_Canvas
   ▼
[ Tier 3: 相互リンクとメタデータ構造化 ]
   │  YAML Frontmatter / WikiLinks [[T###]] / タグ分類
   ▼
[ Tier 4: 公式ドキュメントへの昇格 & 自動連携 ]
   │  docs/*.md への転記昇格 / scripts/generate_knowledge_flow_demo.py
```

### 2.1 Tier 1: キャプチャ & スクラッチ (Inbox & Daily)

- **配置場所**: `exports/knowledge_flow/obsidian_vault/00_Inbox/`, `30_Meetings/`
- **用途**: 思考の即時キャプチャ、デイリーメモ (`YYYY-MM-DD.md`)、30_Meetings（会議の生メモ・リアルタイムアジェンダ）。
- **ルール**: 形式にこだわらず最速でメモを残し、週次で整理・分類します。

### 2.2 Tier 2: アーキテクチャ & プロンプトラボ (Design & Experiment)

- **配置場所**: `exports/knowledge_flow/obsidian_vault/10_ADR_Drafts/`, `20_Prompts/`, `40_Canvas/`
- **用途**:
  - **10_ADR_Drafts**: 技術選定やリファクタリング案の決定理由ドラフト。
  - **20_Prompts**: LLMプロンプトの実験、比較ログ、評価基準。
  - **40_Canvas**: アーキテクチャ構成図、UI画面遷移マップ、データ連携フローのビジュアル描画。

### 2.3 Tier 3: 相互リンクとメタデータ構造化 (WikiLinks & Metadata)

- **WikiLink 表記ルール**:
  - WBSタスクへのリンク: `[[T929]]`
  - 課題トラッカーへのリンク: `[[R148]]`
  - 公式ADRへのリンク: `[[ADR-0005]]`
- **YAML Frontmatter 標準規格**:

```yaml
---
id: NOTE-20260805-01
tags: [adr/proposed, prompt/test, wbs/T929]
status: draft # draft | reviewed | promoted
related_wbs: T929
related_issue: R148
author: Antigravity
created_at: 2026-08-05
---
```

### 2.4 Tier 4: 公式ドキュメントへの昇格 (Promotion & Automation)

- **昇格判定プロセス**:
  1. Obsidian 上でドラフト作成・レビュー完了（`status: reviewed`）。
  2. 合意された内容を公式 `docs/*.md` や `data/WBS.tsv` へ転記コミット。
  3. `status` を `promoted` へ変更し、昇格先パス（例: `promoted_to: docs/ARCHITECTURE_DECISION_RECORDS.md`）を明記。
- **スクリプト自動同期**:
  - `python scripts/generate_knowledge_flow_demo.py` を実行することで、最新の WBS サマリー、ADR、マニフェストが `exports/knowledge_flow/obsidian_vault/` へ自動出力されます。

---

## 3. 3ツールレーン体制における運用分担

| レーン | 主な Obsidian 活用役割 | 同期・スクリプト連携 |
| :--- | :--- | :--- |
| **Antigravity + Gemini** | UI/UX画面遷移の Canvas 設計、日本語UI/UXプロンプトの比較実験 | `40_Canvas/`, `20_Prompts/` の作成・検証 |
| **VSCode + Codex** | Obsidian Vault への WBS・ADR 自動書き出しスクリプトの保守 | `scripts/generate_knowledge_flow_demo.py` |
| **VSCode + Claude Code** | ドラフトノートのレビュー、公式 `docs/` への昇格、リンク整合性の監査 | `scripts/audit_docs_reference_integrity.py` |

---

## 4. セキュリティ & ガバナンス規律

> [!CAUTION]
> **機密情報・認証情報の投入厳禁**
> 1. API キー、サービスアカウント秘密鍵、OAuth トークン、パスワードを Obsidian 内に記述することは厳格に禁止します。
> 2. 個人情報（実氏名、個人の連絡先、要配慮個人情報）を直接メモに記録することは禁止し、必ず匿名ラベル（例: `TALENT-001`）に置き換えて記述します。
