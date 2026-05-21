# Codex 継続作業メモ

作成日: 2026-05-21

## 背景

Antigravity で利用している Gemini 側で baseline quota 制限が発生したため、2026/5/27 18:48:10 の quota refresh までは VSCode + Codex で実装・整理・検証を継続する。

表示された制限メッセージ:

```text
Your plan's baseline quota will refresh on 2026/5/27 18:48:10.
```

## 現在の運用方針

- Antigravity + Gemini の quota が残っている通常時は、Antigravity を主作業環境として使う。
- Antigravity 側で Gemini quota 制限に達したら、VSCode + Codex に切り替えて開発を継続する。
- コード実装、ドキュメント整備、ローカル検証、Git 操作は Codex で継続する。
- FastAPI アプリは Gemini API が使えない場合でも mock fallback で動作する。
- Google Sheets / Calendar / Drive 連携は `authorized_user.json` を使い、Workspace アカウント `k-umezawa@ml-mightylink.com` で継続する。
- Gemini API の quota を消費したくない場合は `AI_FORCE_MOCK=1` を付けてサーバーを起動する。

## VSCode + Codex への切り替え手順

1. VSCode で本プロジェクト `mighty-link-ai-connect` を開く。
2. Codex に作業を引き継ぎ、実装・検証・ドキュメント更新を進める。
3. Gemini quota 中は `AI_FORCE_MOCK=1` で FastAPI を起動し、AI fallback と Sheets 連携の確認を行う。
4. 作業完了後は Codex で commit / push / main 反映まで行う。

## quota-safe 起動

PowerShell:

```powershell
$env:AI_FORCE_MOCK = "1"
python src/app.py
```

バックグラウンド起動:

```powershell
$env:AI_FORCE_MOCK = "1"
Start-Process -WindowStyle Hidden -FilePath python -ArgumentList "src/app.py" -WorkingDirectory .
```

## 確認方法

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health
```

期待値:

```json
{
  "status": "healthy",
  "sheets_live": true,
  "gemini_live": false,
  "ai_mode": "deterministic_fallback",
  "ai_force_mock": true
}
```

## Gemini 復帰時

quota refresh 後に live Gemini を使う場合は、`AI_FORCE_MOCK` を未設定に戻し、`GEMINI_API_KEY` を設定してから `python src/app.py` を起動する。

## 2026-05-21 作業ログ: バックエンド AI 基盤肉付け

Gemini quota 復帰待ちの間に、VSCode + Codex で `src/app.py` の AI fallback を固定 mock から deterministic pipeline へ拡張した。

実施内容:

- `ParsedProfile` データ構造を追加。
- スキル分類辞書 `SKILL_TAXONOMY` を追加。
- `/api/parse` で structured profile を返すようにした。
- `/api/match` で matched skills / missing skills / 4軸スコア根拠を含む structured payload を返すようにした。
- Gemini live 復帰時に deterministic pre-parse / pre-score を prompt context として渡す準備を入れた。
- カレンダー同期スクリプトを冪等化し、既存イベントを更新して重複作成しにくい動きにした。
- WBS に `T304` を追加し、Google Sheets の `Mighty-Link WBS` タブへ同期した。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ同期した。時間指定イベントの比較を正規化し、重複していた社長報告会イベントを整理したうえで、最終結果は `Success: 6, Updated: 6, Failed: 0`。

関連ドキュメント:

- [BACKEND_AI_PIPELINE.md](BACKEND_AI_PIPELINE.md)
- [WBS.md](WBS.md)

## 2026-05-21 作業ログ: AI監査ログと再同期

deterministic pipeline の判定根拠を後から確認・改善できるよう、`src/app.py` にローカル監査ログ基盤を追加した。

実施内容:

- `/api/parse` と `/api/match` のレスポンスに `audit_event_id` を追加。
- `data/audit/ai_audit.jsonl` へ、AI mode、スコア、matched/missing skills、短い excerpt、digest を保存するようにした。
- 原文全文は保存せず、監査ログ本体 `data/audit/*.jsonl` は `.gitignore` 対象にした。
- `data/audit/.gitkeep` を追加し、ログ保存先ディレクトリのみ Git 管理できるようにした。
- `/api/audit/recent?limit=10` を追加し、直近の AI 判定イベントを確認できるようにした。
- 英語入力の `8 years experience` も経験年数として抽出できるよう、経験年数パーサーを拡張した。
- WBS に `T305` を追加し、AI監査基盤の実装完了を反映した。

検証結果:

- `python -m compileall src scripts` 成功。
- `AI_FORCE_MOCK=1` で FastAPI を起動し、`/api/health` が `ai_mode: deterministic_fallback` を返すことを確認。
- `/api/parse` が `structured_profile.experience_years: 8` と `audit_event_id` を返すことを確認。
- `/api/match` が `final_score: 97`、`matched_skills`、`missing_skills`、`audit_event_id` を返すことを確認。
- `/api/audit/recent?limit=3` が直近監査イベントを返すことを確認。
- Google Sheets の `Mighty-Link WBS` タブへ WBS 14 行を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 6, Updated: 6, Failed: 0`。

## 2026-05-21 作業ログ: 公開デモURL保護

社長共有済みの公開URL `https://kanta13jp1.github.io/mighty-link-ai-connect/` が README fallback になるデグレを防ぐため、GitHub Pages root 配信を明示的に保護した。

実施内容:

- root `index.html` が GitHub Pages の公開デモ本体であることを手順書へ明記。
- `scripts/verify_public_demo.py` を追加し、root `index.html` と公開URLの UI 必須マーカーを検証できるようにした。
- `.github/workflows/public-demo-guard.yml` を追加し、`main` / `master` への push と PR で root `index.html` の存在・UIマーカーを検証するようにした。
- WBS に `T306` を追加し、公開デモ保護を完了タスクとして記録した。
- Google Sheets の `Mighty-Link WBS` タブへ WBS 15 行を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 6, Updated: 6, Failed: 0`。

公開URLを触る前後の必須コマンド:

```powershell
python scripts/verify_public_demo.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

## 2026-05-21 作業ログ: CATS型WBSスプレッドシート改善

添付参考ファイル `【次期CATS】WBS_分析計画工程(後半).xlsx` を確認し、Google Sheets の WBS 表示を単純一覧から CATS 型の管理表へ改善した。

実施内容:

- `scripts/sync_wbs_to_sheets.py` を拡張し、`data/WBS.tsv` から階層WBS表示を自動生成するようにした。
- `Mighty-Link WBS` タブにタイトル帯、サマリーKPI、フェーズ行、`WBS#` / `Lv` / `WP` / 予定開始日 / 予定終了日 / 予定工数 / 進捗率 / アラート列を追加。
- `WBS Summary` タブを追加し、フェーズ別の総数・完了数・未着手数・完了率・期間を自動集計。
- `WBS Timeline` タブを追加し、タスク別の予定期間・進捗率を横断確認できるようにした。
- 固定ヘッダー、フィルタ、結合セル、列幅、行高、ステータス/アラートの条件付き色分けを Google Sheets API の batch update で適用。
- WBS に `T307` を追加し、CATS型WBSスプレッドシート改善を完了タスクとして記録。

同期・検証:

- Google Sheets へ `16 source rows` / `27 hierarchical WBS display rows` を同期済み。
- `Mighty-Link WBS`, `WBS Summary`, `WBS Timeline` の 3 タブ作成・更新を確認済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 6, Updated: 6, Failed: 0`。
- `python -m compileall src scripts` 成功。
- 公開デモガード `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。

## 2026-05-21 作業ログ: 6/2社長プレゼン準備WBS追加

6/2 の社長打ち合わせまでは、実際の企画・サービス内容を決め打ちせず、社長が判断しやすい材料を準備する方針に切り替えた。

実施内容:

- WBS に `6. 社長プレゼン準備` フェーズを追加。
- `T601` から `T609` まで、目的整理、デモ構成、安定稼働確認、資料骨子、選択肢整理、運用論点、想定QA、最終リハーサル、決定事項反映準備を追加。
- `docs/CEO_PRESENTATION_PREP_2026-06-02.md` を作成し、6/2の目的、当日までに用意するもの、推奨プレゼン構成、デモ導線、決める事項/決めない事項、想定QA、当日後の反映テンプレートを整理。
- Google Calendar 同期対象に `フェーズ6: 社長プレゼン準備` と `社長プレゼン最終リハーサル` を追加。
- `SETUP_GUIDE.md`, `PROJECT_STRUCTURE.md`, `README.md`, `WBS.md` を更新。
- Google Sheets へ `25 source rows` / `37 hierarchical WBS display rows` を同期済み。
- `WBS Summary` の合計行がフェーズ6を含むことを確認済み。合計は `24 tasks / 完了12 / 実行中1 / 未着手11 / 完了率50%`。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。フェーズ6と最終リハーサルを新規作成し、最終結果は `Success: 8, Updated: 6, Failed: 0`。

運用方針:

- 6/2までは「確定サービス資料」ではなく、「決定のための資料」に留める。
- 社長決定後、`T609` の枠でWBS、Calendar、Git、作業ログへ即反映する。

## 2026-05-21 作業ログ: 社長プレゼン判断材料の追加整備

6/2 までは企画・サービス内容を決め打ちしない前提を保ちながら、社長への説明と当日の意思決定が一気に進むように、プレゼン準備WBSをさらに具体化した。

実施内容:

- WBS に `T610` から `T615` までを追加。
- 追加タスクは、スライド化素材、判断マトリクス、議事録テンプレート、デモバックアップ、事前送付メモ、決定後ロードマップ枠。
- `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md` を追加し、スライド構成案、判断マトリクス、当日質問リスト、議事録テンプレート、デモ障害時の代替導線を整理。
- `docs/CEO_PRESENTATION_PREP_2026-06-02.md`, `docs/SETUP_GUIDE.md`, `docs/PROJECT_STRUCTURE.md`, `docs/WBS.md`, `README.md` を更新し、追加資料と運用手順へ反映。
- Google Calendar 同期対象に `社長プレゼン判断材料レビュー` と `社長向け事前共有メモ作成` を追加。

同期・検証:

- `data/WBS.tsv` は `30` タスク、全行 `10` 列であることを確認。
- `python -m compileall src scripts` 成功。
- `python scripts/verify_public_demo.py` 成功。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。
- Google Sheets へ `31 source rows` / `43 hierarchical WBS display rows` を同期済み。
- `WBS Summary` の合計は `30 tasks / 完了15 / 実行中1 / 未着手14 / 完了率50%`。
- フェーズ6は `15 tasks / 完了4 / 実行中1 / 未着手10 / 完了率27%`。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 10, Updated: 8, Failed: 0`。

運用方針:

- 6/2 までは判断材料パックを確定資料ではなく比較・確認用のドラフトとして扱う。
- 6/2 の決定後、`T609`, `T612`, `T615` を使って WBS、Calendar、Git、作業ログへ即時反映する。

## 2026-05-21 作業ログ: NotebookLM / Slack / Notion / Obsidian 開発フロー追加

6/2 の社長打ち合わせに向け、NotebookLM、Slack、Notion、Obsidian を正式実装ではなく「開発フロー候補・判断材料」として整理した。

実施内容:

- WBS に `T616` から `T623` を追加。
- 追加タスクは、開発フロー設計、NotebookLM連携、Slack連携、Notion連携、Obsidian連携、連携デモ導線、権限・情報管理、連携採用判断。
- `docs/DEVELOPMENT_KNOWLEDGE_FLOW.md` を追加し、ツール別の役割、投入する情報/投入しない情報、推奨フロー、6/2で決める確認事項、セキュリティルールを整理。
- `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md` に、NotebookLM / Slack / Notion / Obsidian の比較表と社長確認事項を追加。
- `docs/CEO_PRESENTATION_PREP_2026-06-02.md`, `docs/SETUP_GUIDE.md`, `docs/PROJECT_STRUCTURE.md`, `docs/WBS.md`, `README.md` を更新し、開発ナレッジ連携フローを作業手順に反映。
- Google Calendar 同期対象に `開発ナレッジ連携フロー整理` と `連携ツール採用判断レビュー` を追加。

同期・検証:

- `data/WBS.tsv` は `38` タスク、全行 `10` 列であることを確認。
- `python -m compileall src scripts` 成功。
- `python scripts/verify_public_demo.py` 成功。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。
- Google Sheets へ `39 source rows` / `51 hierarchical WBS display rows` を同期済み。
- `WBS Summary` の合計は `38 tasks / 完了19 / 実行中1 / 未着手18 / 完了率50%`。
- フェーズ6は `23 tasks / 完了8 / 実行中1 / 未着手14 / 完了率35%`。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 12, Updated: 10, Failed: 0`。

運用方針:

- 6/2 までは Slack / Notion への自動投稿や外部API連携を確定実装しない。
- NotebookLM は資料要約・想定QA生成の候補、Slack は通知候補、Notion は議事録/意思決定DB候補、Obsidian はローカル思考メモ候補として提示する。
- 社長決定後、採用するツールだけを実装WBSへ昇格する。

## 2026-05-21 作業ログ: 開発ナレッジ連携デモ実装

社長に「実際にやった状態」を見せられるよう、NotebookLM、Slack、Notion、Obsidian の連携を安全なローカル成果物生成として実装した。

実施内容:

- `scripts/generate_knowledge_flow_demo.py` を追加。
- FastAPI に `/api/knowledge-flow/generate` と `/api/knowledge-flow/status` を追加。
- `exports/` を `/exports` として配信し、ローカルUIから生成成果物へアクセスできるようにした。
- 公開デモ/ローカルUIに `開発ナレッジ連携デモ` セクションを追加。
- `exports/knowledge_flow/` に以下を生成。
  - `notebooklm_source_pack.md`
  - `slack_ceo_update.md`
  - `notion_decision_log.csv`
  - `notion_backlog_import.csv`
  - `CEO_KNOWLEDGE_FLOW_DEMO_GUIDE.md`
  - `obsidian_vault/`
- WBS に `T624` から `T631` を追加し、生成スクリプト、NotebookLM/Slack/Notion/Obsidian実体化、UI/APIデモ、成果物検証を管理対象にした。
- `docs/DEVELOPMENT_KNOWLEDGE_FLOW.md`, `docs/CEO_PRESENTATION_PREP_2026-06-02.md`, `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md`, `docs/SETUP_GUIDE.md`, `docs/PROJECT_STRUCTURE.md`, `docs/WBS.md`, `README.md` を更新した。

検証:

- `python scripts/generate_knowledge_flow_demo.py` 成功。
- `python -m compileall src scripts` 成功。
- FastAPI TestClient で `/api/knowledge-flow/status` と `/api/knowledge-flow/generate` が `200` を返すことを確認。
- ローカル `http://127.0.0.1:8000/` が `knowledge-flow-demo`, `generateKnowledgeFlowArtifacts`, `NotebookLM` を含むことを確認。
- 既存のローカルサーバーを再起動し、`/api/knowledge-flow/generate` が成功することを確認。
- `python scripts/verify_public_demo.py` 成功。

同期結果:

- Google Sheets へ `47 source rows` / `59 hierarchical WBS display rows` を同期済み。
- `WBS Summary` の合計は `46 tasks / 完了27 / 実行中1 / 未着手18 / 完了率59%`。
- フェーズ6は `31 tasks / 完了16 / 実行中1 / 未着手14 / 完了率52%`。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 13, Updated: 12, Failed: 0`。

運用方針:

- 6/2 までは、Slack投稿やNotionページ作成は自動実行せず、投稿案・CSV・vaultとして見せる。
- 社長決定後、採用するツールだけ外部API連携や正式運用WBSへ昇格する。

## 2026-05-21 作業ログ: CLI/MCP連携証跡とGitHub Issues追加

社長に「実際に連携した状態」を説明できるよう、外部サービスへ秘密情報を出さない範囲でCLI/MCP連携を実施した。

実施内容:

- GitHub CLIで `ceo-demo`, `knowledge-flow`, `wbs`, `github-project`, `integration` ラベルを作成/更新。
- GitHub Issuesに `#1` から `#6` を起票し、NotebookLM、Slack、Notion、Obsidian、GitHub Project、WBS連携のタスクを追加。
- `gh project list --owner kanta13jp1 --format json` を実行し、`read:project` スコープ不足でProject連携が止まることを確認。
- Google Drive MCPで `exports/knowledge_flow/notebooklm_source_pack.txt` をGoogle Docsへ変換。
- Notion MCPで `Mighty Skill-Bridge CEO Demo Integration Evidence 2026-06-02` を作成。
- Slack CLIは未検出、送信MCPツールも本セッションで露出しなかったため、投稿案と投稿先確認をIssue #2 / WBS `T636` に分離。
- Obsidian vaultに `.obsidian/app.json` と `.obsidian/appearance.json` を追加し、ローカルvaultとして開きやすい状態にした。
- WBSに `T632` から `T641` を追加した。
- `docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md` と `exports/knowledge_flow/integration_evidence.md` を追加した。

連携URL:

- Google Docs: https://docs.google.com/document/d/1J3spIzQTq5eZ2RGx6K_knt6I3c0GtPDMPhKfBGwnMvI
- Notion: https://www.notion.so/3671d736b9db818aaa33da0a5f1a3951
- GitHub Issues: https://github.com/kanta13jp1/mighty-link-ai-connect/issues

残タスク:

- GitHub Projectは `gh auth refresh -s read:project` 後にProject取得/作成とIssue配置を行う。
- Slackは投稿先チャンネルと社長共有範囲の確認後、connectorまたはWebhookで正式連携する。

同期・検証:

- `data/WBS.tsv` は `56` タスク、全行 `10` 列であることを確認。
- `python -m compileall src scripts` 成功。
- FastAPI TestClient で `/api/health`, `/api/knowledge-flow/status`, `/api/knowledge-flow/generate` が `200` を返すことを確認。
- `python scripts/verify_public_demo.py` 成功。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。
- Google Sheets へ `57 source rows` / `69 hierarchical WBS display rows` を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 15, Updated: 13, Failed: 0`。
