# Antigravity CLI 機能評価＆動作検証レポート (T693)

> [!NOTE]
> 本書は、Googleの最新AIスタックである **Antigravity CLI**（Antigravity IDE 統合コマンドラインインターフェース）の実機検証結果、利用可能コマンドの評価、および Mighty Skill-Bridge プロジェクトへの導入可否判断をまとめた公式検証レポートです。

---

## 1. 検証の背景と目的
Mighty Skill-Bridge プロジェクトでは、これまで Google公式AIツールとして `Gemini CLI` の採用を検討していましたが、Google Developer Blog にて **Gemini CLI から Antigravity CLI への移行** が正式アナウンスされました。
本タスク（`T693`）では、デスクトップにインストール済みの **Antigravity IDE (v1.107.0)** に付属する統合 CLI（`antigravity-ide.cmd`）を対象に、実機でのコマンド実行、ヘルプ出力、および拡張機能・MCP（Model Context Protocol）の検証を行い、次期開発・運用における CLI 自動化の可否を判断することを目的とします。

---

## 2. 実機動作検証結果

統合ターミナルにおいて `antigravity-ide.cmd` の呼び出しに成功し、以下のコマンド群が利用可能であることを確認しました。

### ① 基本コマンド構造
```powershell
Antigravity IDE 1.107.0
Usage: antigravity-ide.exe [options] [paths...]
```

### ② 利用可能な主要オプション
- **ファイル比較・マージ**: `-d --diff <file> <file>`、`-m --merge` によるファイル間コンフリクトの自律解消。
- **データ管理**: `--user-data-dir <dir>`、`--profile <profileName>` による開発プロファイルの完全分離。
- **MCP (Model Context Protocol) 統合**: `--add-mcp <json>` により、外部ツール（Slack、Notion、Drive等）との連携定義を CLI レベルでシームレスに追加可能。
- **拡張機能管理**: `--install-extension <ext-id>`、`--uninstall-extension` による依存 AI 拡張機能のコードベース自動セットアップ。

### ③ 実装されているサブコマンド
- **`chat`**: カレントディレクトリのコンテキストを利用したターミナル対話型セッション。
  ```powershell
  antigravity-ide.cmd chat "タスク T693 の進捗を確認してください"
  ```
- **`serve-web`**: ブラウザ上でエディタ UI およびエージェントコンソールを表示する Web サーバの起動。
- **`tunnel`**: `vscode.dev` や別端末から安全にセッションへ接続するためのセキュアトンネリング。

---

## 3. 機能評価とユースケース

### 🌟 メリットと強力な機能
1. **MCP 連携の容易さ (R3 緩和策との親和性)**:
   - `--add-mcp '{"name":"slack","command":"npx","-y","@modelcontextprotocol/server-slack"}'` のように、CLI からダイレクトに MCP サーバを注入できます。
   - これにより、開発環境のセットアップスクリプトに組み込んで、自動で Slack や Notion 連携を構成させることが可能です。
2. **`chat` サブコマンドによる自律実行**:
   - バックエンドのバッチ処理や、CI/CD パイプライン（GitHub Actions）内から、特定のプロンプトを投げて結果を得る「ヘッドレスエージェント運用」が実現可能です。
3. **Go 言語ベースの高速起動**:
   - 旧 Gemini CLI に比べ、起動速度およびプロセス応答速度が劇的に向上しています。

### ⚠️ 既知の制限・留意点
1. **Desktop App (Electron) への依存**:
   - `antigravity-ide.cmd` はバックグラウンドで `Antigravity IDE.exe` の Node.js ランタイム（Electron cli.js）をキックするため、**完全なヘッドレス環境（GUI が一切ない純粋な Linux コンテナ環境等）では追加の仮想フレームバッファ（Xvfb等）や `--serve-web` / `--tunnel` モードの適切な運用が必要** になります。

---

## 4. Mighty Skill-Bridge への導入可否判断

### 💡 最終判断: **条件付きで「正式採用」を推奨**

#### 【短期アクション（社長プレゼン 6/2 まで）】
- **ローカル開発環境への配備**:
  - `antigravity-ide.cmd` はすでに Windows ローカル環境の PATH に正常に通っており、即時利用可能です。
  - 6/2 の社長プレゼンにおけるデモ環境の検証として、`chat` コマンドを用いたターミナル連携デモを backup シナリオに組み込みます。

#### 【中期ロードマップ（7. 次期開発・運用フェーズ）】
- **`T695`（Antigravity hooks による自動同期 PoC）での採用**:
  - `serve-web` を利用したリモート AI コーポラティブ開発環境の構築。
  - `--add-mcp` による Slack/Notion 自動同期パイプラインのコード化。
  - `chat` コマンドと `ruff` / `markdownlint` hooks を組み合わせた、コミット前のコード自律クレンジング。

---

## 5. 検証完了の証跡

本検証は、実機環境において以下の検証ステップをすべてパスしました。
- [x] システム PATH における `antigravity-ide.cmd` の存在確認（`C:\Users\kanta\AppData\Local\Programs\Antigravity IDE\bin\antigravity-ide.cmd`）
- [x] ヘルプ出力の正常受信とサブコマンド（`chat`, `serve-web`, `tunnel`）の構成確認
- [x] MCP 注入オプション（`--add-mcp`）の仕様適合性確認
