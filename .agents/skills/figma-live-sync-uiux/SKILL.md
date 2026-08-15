---
name: figma-live-sync-uiux
description: "Execute end-to-end Figma live design collaboration, direct canvas automation via Live Plugin Bridge, REST API comments/variables sync, Untitled UI/Linear-styled wireframe generation, and bidirectional code-to-production deployment pipeline."
---

# Figma Live Sync & UI/UX Automation Skill (`figma-live-sync-uiux`)

このスキルは、**Antigravity と Figma（Web版 / デスクトップ版 / Slides）をリアルタイムに双方向接続**し、
Figma キャンバスへの直接自動描画、Untitled UI / Linear 基準のワイヤーフレーム生成、Figma 変更のコード（`index.html`）自動反映、本番デプロイ（Firebase / Cloud Run）までを一貫して自動遂行するためのプロトコルです。

---

## 🏗️ システムアーキテクチャ

```mermaid
graph TD
    subgraph Antigravity_AI[Antigravity AI Copilot]
        CLI[scripts/send_to_figma.py]
        Server[scripts/figma_bridge_server.py (ws://localhost:9099)]
        Generator[scripts/generate_figma_wireframes.py]
        REST[Figma REST API Client]
    end

    subgraph Figma_Environment[Figma Platform]
        Plugin[Antigravity Figma Live Bridge Plugin (code.js + ui.html)]
        Canvas[Figma Canvas (Design / FigJam / Slides)]
        Comments[Figma Comments & Variables API]
    end

    subgraph Production_Codebase[Web Application Codebase]
        HTML[index.html / src/index.html]
        Tests[tests/ (860+ Test Suite)]
        Prod[Live Domain: https://mightylink-app.com/]
    end

    CLI --> Server
    Server <-->|WebSocket| Plugin
    Plugin -->|Figma Plugin API| Canvas
    REST -->|POST /comments| Comments
    Generator --> CLI
    Canvas -.->|Design Tokens & Layout| HTML
    HTML --> Tests
    Tests --> Prod
```

---

## 🎯 トリガー条件

以下の指示やキーワードを受け取った際に自動発動します：
- 「Figmaと連携して」「Figma上でワイヤーフレームを作成して」
- 「Figmaのワイヤーフレームをかっこよく改善して」
- 「FigmaプラグインBridgeを起動して」「Figmaキャンバスに直接描画して」
- 「Figmaのデザイン変更をサイトに反映して」
- 「Figmaにレビューコメントを投稿して」

---

## 📋 5ステップ標準実行プロトコル

### Step 1: Figma 認証 & 疎通確認
1. 環境変数 `FIGMA_ACCESS_TOKEN`（PAT）および `C:\Users\kanta\.gemini\config\mcp_config.json` の設定を確認。
2. Figma REST API (`https://api.figma.com/v1/me`) で疎通確認を実行。
3. 対象ファイル URL から `file_key`（例: `Wc4oQrhWv4tm5gZnaO4lxl`）を抽出。

### Step 2: Live Plugin Bridge サーバーの起動
1. バックグラウンドで Bridge サーバーを起動：
   ```powershell
   python scripts/figma_bridge_server.py
   ```
2. Figma 上で `tools/figma-bridge-plugin/manifest.json` をインポートし、プラグインを実行。
3. プラグイン UI が `[● 接続中 (Live)]` になったことを確認。

### Step 3: ワイヤーフレームの直接生成 & 自動描画
1. 世界最高峰（Untitled UI / Linear / Apple HIG）基準のクリーンな SVG ワイヤーフレームを生成：
   ```powershell
   python scripts/generate_figma_wireframes.py
   ```
2. Live Bridge 経由で Figma キャンバスへ直接プッシュ：
   ```powershell
   python scripts/send_to_figma.py --svg exports/figma_wireframes/mighty_link_full_wireframe_artboard.svg
   ```
3. Figma キャンバス上へライブトースト通知を発行：
   ```powershell
   python scripts/send_to_figma.py --notify "✨ プレミアムSaaSワイヤーフレームを直接描画しました！"
   ```

### Step 4: Figma デザインのコード反映
1. Figma 上で決定・修正された UI コンポーネント（Bento Grid KPI カード、スキルタグチップス、候補者アバター等）を `index.html` および `src/index.html` に適用。
2. デザインのアクセシビリティ（WCAG 2.2 AAA、色覚シンボル）とレスポンシブ（モバイルボトムシート）を保証。

### Step 5: プリフライト検証 & 本番デプロイ
1. 全 28 整合ガードおよびフルテストスイート（860+ 件）を実行：
   ```powershell
   python scripts/run_lane_preflight.py
   python -m pytest tests/
   ```
2. Git コミット＆プッシュで GitHub Actions CI/CD をトリガーし、本番環境（`https://mightylink-app.com/`）へ即座にデプロイ・反映。
3. ユーザーへ本番 URL と更新確認手順（Ctrl + F5）を案内。

---

## 🛠️ コアスクリプト・ツール資産

| ツール / ファイル | パス | 役割 |
| :--- | :--- | :--- |
| **Figma Live Plugin** | [`tools/figma-bridge-plugin/`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/tools/figma-bridge-plugin/) | Figma Canvas 内で動作する WebSocket 連携プラグイン |
| **Bridge Server** | [`scripts/figma_bridge_server.py`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/scripts/figma_bridge_server.py) | `ws://localhost:9099` で常時待機するローカルプロキシ |
| **CLI 送信ヘルパー** | [`scripts/send_to_figma.py`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/scripts/send_to_figma.py) | SVG 描画・色変更・通知を 1 コマンドで Figma へ送信 |
| **ワイヤーフレーム生成** | [`scripts/generate_figma_wireframes.py`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/scripts/generate_figma_wireframes.py) | Untitled UI / Linear 基準のベクター SVG を自動生成 |
| **デザイントークン監査** | [`scripts/audit_figma_design_sync.py`](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/scripts/audit_figma_design_sync.py) | プリフライト第28番目の品質整合ガード |
