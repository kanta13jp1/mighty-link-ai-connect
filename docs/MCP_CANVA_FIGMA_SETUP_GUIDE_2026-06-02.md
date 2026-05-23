# Canva / Figma MCP セットアップ + 自動化フロー (HANDOFF-14 自動化版)

作成日: 2026-05-23
オーナー: VSCode + Claude Code レーン (docs / セットアップ手順) / 実 MCP 接続は人間 (寛太) + Antigravity / Codex / Claude Code が並走実行
対応 WBS: **T658-mcp-extend** (Canva/Figma MCP による自動化)
関連: [CANVA_FIGMA_GUIDE](CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md) (T658-extend、手動手順) / [MULTI_AI_WORKFLOW](MULTI_AI_WORKFLOW.md) / [PREP](CEO_PRESENTATION_PREP_2026-06-02.md)

---

## このドキュメントの位置づけ

[CANVA_FIGMA_GUIDE](CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md) は **手動** で Canva/Figma を操作する手順 (30 分作業)。本書は **MCP (Model Context Protocol) による自動化** で手作業をゼロにする手順書。

ユーザー (2026-05-23) より「Figma MCPや、Canva MCPを使って手動作業を自動化できませんか?」と要望。両 MCP の公式提供を verify-first で確認:

| MCP | 公式提供 | エンドポイント | コスト | 状況 |
| --- | --- | --- | --- | --- |
| **Canva MCP (AI Connector)** | 公式 ([canva.dev/docs/mcp](https://www.canva.dev/docs/mcp/)) | `https://mcp.canva.com/mcp` (remote) | 全プラン無料、Enterprise でブランドキット autofill | 一般提供 |
| **Figma MCP Server** | 公式 ([developers.figma.com/docs/figma-mcp-server](https://developers.figma.com/docs/figma-mcp-server/)) | Remote (推奨) / `http://127.0.0.1:3845/mcp` (Dev Mode local) | beta 期間中無料、将来 usage-based 課金 | beta |

両者とも **Claude Code 公式サポート**。本書では 3 ツール (Claude Code / Cursor / Claude Desktop) いずれからも MCP を呼べる手順を提供。

---

## 1. Canva MCP セットアップ (推奨パス、無料)

### 1.1 前提

- Canva アカウント (`k-umezawa@ml-mightylink.com` 推奨、無料プランで OK)
- Claude Code (本セッションの環境) または Claude Desktop / Cursor / ChatGPT
- npx 実行可能環境 (Node.js 18+)

### 1.2 Claude Code 設定 (公式構文、verify-first 検証済 2026-05-23)

公式 [Claude Code MCP docs](https://code.claude.com/docs/en/mcp) の `claude mcp add` CLI 構文に従う:

#### 推奨パス: HTTP transport (Canva MCP は HTTP ネイティブ対応)

```bash
# 公式構文: claude mcp add --transport http <name> <url>
claude mcp add --transport http canva https://mcp.canva.com/mcp
```

#### フォールバック: stdio transport via mcp-remote

HTTP が詰まる場合 / レガシー MCP クライアントでの動作確認用:

```bash
# 公式構文: claude mcp add [options] <name> -- <command> [args...]
# 注意: -- (double dash) で server name と command を分離必須
claude mcp add canva -- npx -y mcp-remote@latest https://mcp.canva.com/mcp
```

または `~/.claude.json` / `.mcp.json` に直接追記 (HTTP 版):

```json
{
  "mcpServers": {
    "canva": {
      "type": "http",
      "url": "https://mcp.canva.com/mcp"
    }
  }
}
```

stdio 版の JSON 設定:

```json
{
  "mcpServers": {
    "canva": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.canva.com/mcp"]
    }
  }
}
```

### 1.2.1 認証フロー

1. 上記コマンド実行後、Claude Code セッション内で `/mcp` を実行
2. `canva` が `Authentication needed` 状態で表示される
3. `/mcp` メニューで `Authenticate canva` を選択 → ブラウザが起動
4. Dynamic Client Registration (DCR) フローで `k-umezawa@ml-mightylink.com` の Canva アカウントへ OAuth 認可
5. 承認後、トークンが Claude Code の MCP 認証ストア (`~/.claude/` 配下、`.gitignore` 済) に保存される
6. `/mcp` で `canva` が `connected` になることを確認

### 1.3 利用可能な機能 (プラン別)

[Canva MCP Tools](https://www.canva.dev/docs/mcp/tools/) より:

| 機能 | 全プラン | Pro+ | Enterprise |
| --- | --- | --- | --- |
| デザイン生成 (text-to-design) | ✓ | ✓ | ✓ |
| デザイン編集 (テキスト/画像/レイアウト) | ✓ | ✓ | ✓ |
| デザイン検索 (library 内) | ✓ | ✓ | ✓ |
| エクスポート (PDF/PNG/JPG/PPTX/MP4) | ✓ | ✓ | ✓ |
| コメント追加 | ✓ | ✓ | ✓ |
| アセットアップロード | ✓ | ✓ | ✓ |
| **リサイズ** (新サイズへ自動調整) | ✗ | ✓ | ✓ |
| **テンプレ autofill** (brand template に差し込み) | ✗ | ✗ | ✓ |
| **ブランドキット** (色/フォント自動適用) | ✗ | ✗ | ✓ |

**本プロジェクトへの impact**: Mighty-Link が Canva Enterprise でなければ、**ブランドキット自動適用は MCP 経由で不可**。代替策:
- 寛太が Canva 上で Mighty Skill-Bridge ブランドカラーを「個人のブランドキット」として手動登録 (5 分)
- MCP からは「ブランドカラー A の色 #00f0ff を見出しに適用してください」と都度プロンプトで指定

### 1.4 Claude Code から自動化する 8 枚スライド作成プロンプト

セットアップ後、Claude Code セッションで以下のプロンプトを実行 (1 ターンで全 8 枚生成):

```text
Canva MCP を使って、以下の手順で社長プレゼン用デザインを作成してください。

1. 新規プレゼン (16:9、8 枚) を作成、タイトルは「Mighty Skill-Bridge CEO Brief 2026-06-02」
2. 各スライドに以下のテキストを配置 (内容は docs/CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md の 8 枚コピペカードと完全一致):

   Slide 1: 本日決めたいこと — 方針・優先順位・次アクション
   要点 3: (カード Slide 1 参照)
   話すメモ: (スピーカーノートへ)
   社長への質問: (スライド下部にネオンブルー強調)

   Slide 2: 現在の到達点と公開デモ — Seedance シネマティック UI 完成
   ...

   (Slide 3-8 も同様)

3. 全スライドのデザイン:
   - 背景: cyber black #0d0e15
   - 見出し: cool white #f1f5ff
   - 本文: gray white #c5cae0
   - タイトルアクセント: neon blue #00f0ff
   - CTA / 数値強調: neon green #39ff14
   - リスク強調: neon red #ff3366

4. スライド 2-4 には公開デモスクショ用のプレースホルダー (1280x720 透明枠) を右半分に配置

5. 完成後、PPTX と PDF 両方でエクスポート、ダウンロード URL を返してください
```

このプロンプトを Claude Code に渡すと、Canva MCP が:
- `canva_create_design` で新規プレゼン作成
- `canva_edit_design` でテキスト 8 セット投入
- `canva_export_design` で PPTX + PDF 出力
- ダウンロード URL を返す

**所要時間**: 約 2-5 分 (手動 30 分 → 自動 5 分、6 倍速)。

### 1.5 制約と注意

- **OAuth トークン** は Claude Code の MCP 認証ストアに保存される。`.claude/` 配下に **commit しない** (既に `.gitignore` 設定済の `.claude/` ディレクトリ)
- Canva 無料プランの API レート制限あり (具体値は [Canva MCP Tools and rate limits](https://www.canva.dev/docs/mcp/tools/) 参照)
- ブランドテンプレ適用が必要なら Enterprise アップグレードを Q-OPS-09 (月額コスト上限) と合わせて社長判断

---

## 2. Figma MCP セットアップ (代替パス、beta 無料)

### 2.1 前提

- Figma アカウント (Free プラン OK、ただし MCP は Professional 推奨)
- Figma Desktop アプリ (Dev Mode local 使用時のみ必須、Remote なら不要)
- Claude Code

### 2.2 Remote 接続 (推奨)

[Figma Remote MCP Server Installation](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/) より、Claude Code 公式 [mcp docs](https://code.claude.com/docs/en/mcp) の構文で:

```bash
# 公式構文: claude mcp add --transport http <name> <url>
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

または `~/.claude.json` / `.mcp.json`:

```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

接続後、Claude Code セッション内で `/mcp` を実行 → `figma` を `Authenticate` で選択 → ブラウザで Figma アカウント OAuth 認可。

### 2.3 Local Dev Mode (オフライン / プライベートファイル)

機密性が高い Figma ファイルでローカル処理したい場合のみ:

1. Figma Desktop アプリを起動
2. メニュー → Preferences → **Enable Dev Mode MCP Server** をオン
3. ローカルエンドポイント `http://127.0.0.1:3845/mcp` が起動
4. Claude Code 設定で `"url": "http://127.0.0.1:3845/mcp"` を指定

### 2.4 利用可能な機能

- **Frame → コード生成** (Figma → React/Flutter/Swift 等)
- **Figma content の書き戻し**: frames / components / variables / auto layout を Claude から作成・更新可能
- **Make resource retrieval**: Figma Make ファイルからコード context を取得
- **Code Connect**: design system component を維持

**注意**: Figma Slides 専用の MCP コマンドは現時点で公式 docs に未記載 ([Figma Slides](https://www.figma.com/slides/) 自体は 2026 リリース済)。通常の Frame として 16:9 スライドを作成し、export で PPTX 化する代替フローが現実的。

### 2.5 Claude Code から自動化する 8 枚スライド作成プロンプト (Figma 版)

```text
Figma MCP を使って、以下の手順で社長プレゼン用 Figma ファイルを作成してください。

1. 新規 Figma ファイル「Mighty Skill-Bridge CEO Brief 2026-06-02」を作成
2. 1920x1080 (16:9) のフレーム 8 つを縦に配置
3. 各フレームに以下のテキストを配置:
   (docs/CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md の 8 枚コピペカード内容を投入)
4. Color Variables を定義:
   - cyber-black: #0d0e15
   - neon-blue: #00f0ff
   - neon-green: #39ff14
   - cool-white: #f1f5ff
   - gray-white: #c5cae0
   - neon-red: #ff3366
5. 各フレームの背景を cyber-black に、見出しを neon-blue に、本文を gray-white に設定
6. スライド 2-4 には 1280x720 のプレースホルダー frame (枠線 neon-green) を右半分に配置
7. 完成後、全フレームを PNG + PDF で export
```

### 2.6 制約

- Figma MCP は **beta 期間中**、将来 usage-based 課金
- Figma Slides 専用 MCP コマンドが未提供 → 通常 Frame での実装
- Free プランでは編集回数に制限あり (公式 docs で要確認)

---

## 3. 推奨パス決定 (Canva MCP vs Figma MCP)

| 観点 | Canva MCP | Figma MCP |
| --- | --- | --- |
| セットアップ容易度 | ★★★★★ (npx + OAuth) | ★★★★ (Catalog 経由 + OAuth) |
| スライド出力品質 | ★★★★★ (プレゼン特化テンプレ豊富) | ★★★ (Slides MCP 未提供) |
| PPTX 直接 export | ✓ | △ (PDF/PNG 経由) |
| ブランドカラー適用 | △ (Enterprise のみ自動、それ以外は都度指定) | ✓ (Variables で完全制御) |
| Mighty-Link 親和性 | ★★★★ (既存 PPTX と直結) | ★★★ (デザインシステム化に強い) |
| 6/2 までの所要 | 2-5 分 | 5-10 分 |
| 長期再利用性 | ★★★ (Canva 内に閉じる) | ★★★★★ (Variables / Components で資産化) |

**推奨**:
- **6/2 当日プレゼン用**: Canva MCP (即生成、PPTX 直接 export、社長共有しやすい)
- **6/16 以降の長期デザインシステム**: Figma MCP (Variables / Components で資産化、複数プレゼンに展開可能)

両方並行セットアップして使い分けるのが理想。

---

## 4. セッション中の自動化フロー (Claude Code → Canva MCP)

セットアップ完了後、本セッション (or 後続セッション) で実行する完全自動化フロー:

### Step A: MCP 認証確認

```text
[Claude Code セッション内で]
> /mcp list
```

`canva` と `figma` が `connected` になっていることを確認。

### Step B: ソース取得

Claude Code が [exports/knowledge_flow/notebooklm_ceo_slide_outline.md](../exports/knowledge_flow/notebooklm_ceo_slide_outline.md) (NotebookLM 自動生成、2026-05-23 22:23 版) を Read。

### Step C: Canva MCP 実行 (1 ターン)

上記「1.4 Claude Code から自動化する 8 枚スライド作成プロンプト」をユーザーが Claude Code に送信。

### Step D: 成果物保存

Canva MCP が返したダウンロード URL から PPTX/PDF をローカル `exports/knowledge_flow/` 配下に保存:

- `mighty_skill_bridge_ceo_presentation_2026-06-02_canva_mcp.pptx`
- `mighty_skill_bridge_ceo_presentation_2026-06-02_canva_mcp.pdf`

### Step E: 公開デモスクショ差し込み (人間 or Antigravity)

スライド 2-4 のプレースホルダー枠に公開デモスクショを手動 (or HANDOFF-16 経由) で配置。

### Step F: Drive アップロード + Codex 反映

`scripts/upload_notebooklm_docs_to_drive.py` で `k-umezawa@ml-mightylink.com` 所有の Drive にアップロード → 取得した URL を `exports/knowledge_flow/*.json` の `canva_mcp_drive_url` フィールドに追記 (Codex レーンへ handoff)。

### Step G: FINAL_REVIEW_CHECKLIST 更新

[FINAL_REVIEW_CHECKLIST B-2](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) の「PPTX が Drive で開ける」を Canva MCP 版に置換、項目 B-7 を新規追加。

---

## 4.6. 実機実行ログ — Figma MCP で 9 slides 自動生成 (2026-05-24)

寛太様が Figma MCP OAuth 認証完了 → Claude Code から本ガイドの手順を実行し、Figma Slides ファイルを自動生成した実績:

| 項目 | 値 |
| --- | --- |
| **Figma file** | [Mighty Skill-Bridge CEO Brief 2026-06-02](https://www.figma.com/slides/PAQWzAUPoPTy3ibLcOmPDC) |
| **fileKey** | `PAQWzAUPoPTy3ibLcOmPDC` |
| **team** | `tokyofigma01` (team::1404391492263715179) |
| **owner** | kanta13jp@gmail.com (handle: kanta13jp1) |
| **slide count** | 9 (1 title cover + 8 content) |
| **slide size** | 1920×1080 (16:9) |
| **brand colors** | Mighty Skill-Bridge / Seedance cinematic 7 色適用 |
| **embedded image** | Slide 2 (現在の到達点と公開デモ) に公開デモのライブスクショ |

### 実行手順 (再現可能)

```text
1. claude mcp authenticate (Figma)
2. mcp__plugin_design_figma__whoami → planKey 取得
3. mcp__plugin_design_figma__create_new_file --editorType slides --planKey team::... --fileName "..."
4. mcp__plugin_design_figma__upload_assets --fileKey ... --count 1 (POST PNG via curl multipart)
5. mcp__plugin_design_figma__use_figma --code "<JS that creates 9 slides via figma.createSlide() with brand styling + bullets + CTA + image fill>"
```

### Figma Plugin API メモ (実装中に判明)

- `figma.createSlide()` 動作。返値は SLIDE 型 (1920×1080 固定)
- SLIDES ファイルは Page → SLIDE_GRID → SLIDE_ROW → SLIDE 階層
- SLIDE.name は自動採番 ("1", "2" ...) で `slide.name = "..."` のオーバーライドは効かない
- 画像 fill は `{ type: "IMAGE", scaleMode: "FIT"/"FILL"/"CROP"/"TILE", imageHash: "..." }`
  - imageHash は upload_assets の戻り値 (`placedOnNodeId` と一緒に返る `imageHash`)
- フォント: `figma.loadFontAsync({ family: "Inter", style: "Bold"|"Semi Bold"|"Regular" })` で事前ロード必須
- 注意: `figma.slides` は存在しない (figma globals に slides namespace なし)。スライド操作は通常の Plugin API で行う

### Figma MCP Starter プラン制限

- Figma 公式 Starter プランでは get_screenshot の MCP tool call 数に制限あり (本実機実行で `Upgrade your plan` メッセージ受信)
- 制限到達後も use_figma / create_new_file / upload_assets は引き続き動作
- スライド検証は Figma エディタで直接開いて目視推奨 (Drive アップロード等の自動チェックは別途)

---

## 4.5. よくあるエラーと修正 (2026-05-23 実機検証)

寛太が実際にコマンド実行して遭遇したエラーとその修正:

### Error 1: `claude mcp add canva` → `missing required argument 'commandOrUrl'`

```text
PS> claude mcp add canva
error: missing required argument 'commandOrUrl'
```

**原因**: 公式 `claude mcp add` 構文は `<name>` の後に **URL または command を必須引数として渡す**必要がある。`canva` だけだと URL/command が未指定。

**修正**: HTTP transport の場合は `--transport http` + URL を指定:

```bash
claude mcp add --transport http canva https://mcp.canva.com/mcp
```

stdio の場合は `--` セパレーター + command を指定:

```bash
claude mcp add canva -- npx -y mcp-remote@latest https://mcp.canva.com/mcp
```

### Error 2: `npx mcp-remote` → `Usage: npx tsx proxy.ts <https://server-url> ...`

```text
PS> npx mcp-remote
[32972] Usage: npx tsx proxy.ts <https://server-url> [callback-port] [--debug]
```

**原因**: `mcp-remote` パッケージは **サーバー URL を第 1 引数として必須**。引数なしで実行するとヘルプメッセージが出る。

**修正**: URL を引数で渡す:

```bash
npx mcp-remote https://mcp.canva.com/mcp
```

ただし、`mcp-remote` は通常 **Claude Code が内部で起動するもの**で、寛太が手動で叩く必要はない。`claude mcp add canva -- npx -y mcp-remote@latest https://mcp.canva.com/mcp` を実行すると Claude Code が必要なときに自動起動する。

### Error 3: OAuth ブラウザが開かない

`claude mcp add` 直後にブラウザが開かないのは正常 — OAuth 認可は **Claude Code セッション内で `/mcp` 実行** したときに初めて発生する。

```bash
# 1. MCP server 追加 (この時点では認証なし)
claude mcp add --transport http canva https://mcp.canva.com/mcp

# 2. Claude Code セッション起動
claude

# 3. セッション内で /mcp 実行 → Authenticate canva 選択 → ブラウザが起動
> /mcp
```

### Error 4: `/mcp` で `canva: Authentication needed` のまま

ブラウザ認可が完了したのに `/mcp` の表示が古い場合:

```bash
# Claude Code セッションを再起動
exit
claude

# /mcp で再確認
> /mcp
```

または `claude mcp get canva` で OAuth credentials の保存状態を確認可能。

---

## 5. 失敗時のフォールバック

MCP セットアップが詰まった場合の段階的フォールバック:

| 失敗パターン | 原因 | フォールバック |
| --- | --- | --- |
| OAuth 認可ブラウザが開かない | DCR 認証フロー詰まり | 手動 token 生成: [Canva manual auth](https://www.canva.dev/docs/connect/canva-mcp-server-setup/) |
| MCP server 接続できない | ネットワーク / プロキシ | local Dev Mode (Figma) に切り替え |
| Canva 無料プランで機能足りない | テンプレ autofill 不可 | [CANVA_FIGMA_GUIDE 手動手順](CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md) に戻す |
| 全 MCP 詰まり | 時間切れ | 既存 PPTX のまま 6/2 デモ実施、Canva 化は 6/9 までに後追い |

---

## 6. セキュリティ / プライバシー

- **個人情報 / 経歴書のサンプルデータは MCP 経由で外部送信しない** (R9 個人情報リスク準拠)
- Canva / Figma MCP は **公開可能なプレゼンテキストのみ** を流す
- OAuth トークンは `.claude/` 配下に保存され `.gitignore` 済
- 退会・revoke 手順:
  - Canva: https://www.canva.com/settings/apps で連携解除
  - Figma: https://www.figma.com/settings/connected-apps で連携解除
- Workspace アカウント (`k-umezawa@ml-mightylink.com`) で承認すれば履歴が一元管理可

---

## 7. Codex / Antigravity / Claude Code レーン分担

3-tool 体制 ([MULTI_AI_WORKFLOW](MULTI_AI_WORKFLOW.md)) に MCP 自動化を組み込む:

| 工程 | 担当 | 備考 |
| --- | --- | --- |
| MCP セットアップ docs (本書) | Claude Code (完了) | - |
| MCP 接続実行 (`claude mcp add`) | 人間 (寛太) | OAuth 認可は人間ブラウザ必須 |
| Canva MCP 経由でプレゼン自動生成 | Claude Code (本セッション or 後続) | 上記 Step B-D |
| 公開デモスクショ取得 | Antigravity Browser Agent or 人間 | HANDOFF-16 で自動化候補 |
| Drive アップロード + JSON manifest 追記 | Codex | HANDOFF-14 の継続 |
| 6/2 当日デモ操作 | 寛太 | - |

---

## 8. WBS / Issues / 関連 docs

- [data/issues_tracker.tsv](../data/issues_tracker.tsv) の HANDOFF-14 (手動 Canva) を **HANDOFF-14a (手動)** と **HANDOFF-14b (MCP 自動化)** に分岐させる予定 (本書 commit 時に更新)
- 新規 **HANDOFF-17**: Canva MCP セットアップ実行 (寛太、所要 10 分)
- 新規 **HANDOFF-18**: Figma MCP セットアップ実行 (寛太、所要 10 分、Canva 失敗時のバックアップ)
- 本書 commit 後、[CANVA_FIGMA_GUIDE](CEO_PRESENTATION_CANVA_FIGMA_GUIDE_2026-06-02.md) の手順 1 セクションに「MCP 自動化版は本書を参照」のリンクを追加

---

## 9. 更新履歴

| 日付 | 変更者 | 内容 |
| --- | --- | --- |
| 2026-05-23 | Claude Code | 初版作成 (T658-mcp-extend、Canva MCP + Figma MCP セットアップ手順 + 自動化フロー + プラン別機能マトリクス + フォールバック) |
| 2026-05-23 | Claude Code | 寛太の実機検証で発見した CLI 構文エラーを修正。`claude mcp add` の公式構文 (`--transport http <name> <url>` または `<name> -- <command>`) に統一。§4.5 として 4 つの実エラーと修正手順を追加 |
