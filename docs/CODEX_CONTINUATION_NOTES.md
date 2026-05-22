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

- Google Docs: https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit
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

## 2026-05-21 作業ログ: NotebookLMプレゼン資料化とProject認証再試行

プレゼン用資料作成はNotebookLMで進める方針に合わせ、Source Packとは別にPresentation Briefを生成し、Google Docs化した。

実施内容:

- `scripts/generate_knowledge_flow_demo.py` に `notebooklm_presentation_brief.md` / `.txt` 生成を追加。
- Google Drive MCPで `exports/knowledge_flow/notebooklm_presentation_brief.txt` をGoogle Docsへ変換。
- Presentation Brief URL: https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit
- GitHub Issue #7 `NotebookLMでプレゼン資料たたき台を作成する` を起票。
- `gh auth refresh -h github.com -s read:project -s project` を再試行したが、2分でタイムアウト。
- GitHub Issue #8 `GitHub Project OAuthスコープ復旧を完了する` を起票。
- Notion証跡ページにPresentation BriefとIssue #7/#8の追加コメントを残した。
- WBSに `T642` から `T646` を追加した。

残タスク:

- NotebookLMへSource PackとPresentation Briefを投入し、8枚以内のスライド構成、話す要点、想定QAを生成する。
- ユーザー側でGitHub OAuthブラウザ認証を完了し、Project boardへIssue #1-#8を配置する。
- Slack投稿先チャンネルとconnector/CLI送信権限を確認する。

同期・検証:

- `data/WBS.tsv` は `61` タスク、全行 `10` 列であることを確認。
- `python -m compileall src scripts` 成功。
- FastAPI TestClient で `/api/health`, `/api/knowledge-flow/status`, `/api/knowledge-flow/generate` が `200` を返すことを確認。
- `python scripts/verify_public_demo.py` 成功。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。
- Google Sheets へ `62 source rows` / `74 hierarchical WBS display rows` を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 17, Updated: 15, Failed: 0`。

## 2026-05-21 作業ログ: Google Workspaceアカウント固定ガード追加

Google連携が必ず `k-umezawa@ml-mightylink.com` で実行されるよう、OAuthアカウント検証を追加した。

実施内容:

- Drive API `about.user.emailAddress` で `authorized_user.json` の実行アカウントを確認し、`k-umezawa@ml-mightylink.com` と一致することを確認。
- `src/google_workspace_account.py` を追加し、OAuth認証情報のアカウント検証を共通化。
- `scripts/verify_google_workspace_account.py` を追加。
- `scripts/sync_wbs_to_sheets.py`, `scripts/sync_wbs_to_calendar.py`, `scripts/share_resources.py`, `src/app.py` に、同期前のWorkspaceアカウント検証を追加。
- 誤って別Googleアカウントの `authorized_user.json` に差し替わった場合は、Sheets / Calendar / FastAPI同期が停止する。
- WBSに `T647` を追加した。

確認結果:

- `python scripts/verify_google_workspace_account.py` 成功。
- Drive API上の実行アカウント: `k-umezawa@ml-mightylink.com`
- `data/WBS.tsv` は `62` タスク、全行 `10` 列であることを確認。
- Google Sheets へ `63 source rows` / `75 hierarchical WBS display rows` を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 18, Updated: 17, Failed: 0`。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。

## 2026-05-22 作業ログ: Workspace Google Docs再作成

Google DocsホームでNotebookLM用資料が `k-umezawa@ml-mightylink.com` 側に表示されない問題に対応した。

実施内容:

- `scripts/upload_notebooklm_docs_to_drive.py` を追加し、Google Drive MCPではなく `authorized_user.json` のLocal OAuth Drive APIでGoogle Docsを作成/更新する導線にした。
- 実行前に `src/google_workspace_account.py` のガードで `k-umezawa@ml-mightylink.com` を検証するようにした。
- `exports/knowledge_flow/notebooklm_source_pack.txt` と `exports/knowledge_flow/notebooklm_presentation_brief.txt` をWorkspace所有のネイティブGoogle Docsへ変換した。
- Drive APIレスポンスのownerが `k-umezawa@ml-mightylink.com` であることを確認し、`exports/knowledge_flow/google_drive_workspace_docs.json` に保存した。
- WBSに `T648` を追加し、T634/T642の実行エンジンをLocal OAuth Drive APIへ修正した。
- 手順書と証跡ドキュメントのGoogle Docs URLをWorkspace所有Docへ差し替えた。

Workspace Google Docs:

- Source Pack: https://docs.google.com/document/d/1qPjlbvvkfYdw0FrkPMz8JCnMjrIuPy3toEoH6hVriGQ/edit
- Presentation Brief: https://docs.google.com/document/d/1TFCrubKMa17L-ebIiMBPGpekabuEfd9NNQw3rVWpFoI/edit

同期・検証:

- `python scripts/verify_google_workspace_account.py` 成功。
- `python scripts/upload_notebooklm_docs_to_drive.py` 成功。
- Google Sheets へ `64 source rows` / `76 hierarchical WBS display rows` を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 19, Updated: 18, Failed: 0`。
- `python -m compileall src scripts` 成功。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。
- 旧Google Docs IDは `docs/`, `data/`, `exports/`, `scripts/` から除去済み。

## 2026-05-22 作業ログ: docs配下NotebookLM同期導線追加

AIエージェントがNotebookLMから要約された設計情報・ロードマップ情報を取得して開発を進められるよう、`docs/` 配下をNotebookLM source候補へ同期する導線を追加した。

実施内容:

- `scripts/sync_docs_to_notebooklm.py` を追加。
- `docs/*.md` 14件を `k-umezawa@ml-mightylink.com` 所有のGoogle Docsへ同期。
- 同期manifestを `exports/knowledge_flow/notebooklm_docs_manifest.json` へ保存。
- NotebookLM CLI `0.3.4` の存在を確認。
- `notebooklm list` は認証切れで失敗したため、`exports/knowledge_flow/notebooklm_cli_next_steps.md` に再認証手順を保存。
- 再認証後に `notebooklm source add-drive` と `notebooklm ask/summary` を実行し、`exports/knowledge_flow/notebooklm_agent_brief.md` / `.json` を生成する構成にした。
- GitHub Issue #9 / #10 を追加。
- Issue #8 にGitHub Projectの `read:project` スコープ不足の最新状況をコメント。
- Notion証跡ページ配下に `NotebookLM Docs Sync Evidence 2026-05-22` を作成。
- Obsidian vaultにNotebookLM Agent Brief参照導線を追加。
- WBSに `T649` から `T655` を追加。

証跡:

- NotebookLM docs manifest: `exports/knowledge_flow/notebooklm_docs_manifest.json`
- NotebookLM CLI next steps: `exports/knowledge_flow/notebooklm_cli_next_steps.md`
- Notion: https://www.notion.so/3671d736b9db8164b46dc143befa29eb
- GitHub Issue #9: https://github.com/kanta13jp1/mighty-link-ai-connect/issues/9
- GitHub Issue #10: https://github.com/kanta13jp1/mighty-link-ai-connect/issues/10

同期・検証:

- Google Sheets へ `73 source rows` / `85 hierarchical WBS display rows` を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 24, Updated: 24, Failed: 0`。
- NotebookLM CLIは `notebooklm list` 実行時に認証切れを返したため、`notebooklm login` 後の再実行待ち。
- `python -m compileall src scripts` 成功。
- `python scripts/verify_google_workspace_account.py` 成功。
- `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。

残タスク:

- GitHub Projectは `gh auth refresh -s read:project -s project` 後にIssue配置を再実行する。
- Slackは投稿先チャンネルと送信権限を確認後、`exports/knowledge_flow/slack_ceo_update.md` を正式投稿する。

## 2026-05-22 NotebookLM認証完了・要約取得

実施内容:

- upstream `notebooklm login` がGoogle Accounts遷移中断で落ちたため、`scripts/notebooklm_login_workspace.py` を追加した。
- 補助ログイン導線で `k-umezawa@ml-mightylink.com` のNotebookLM CLI認証状態を保存した。
- NotebookLM notebook `75521ea6-6b9b-47b2-9508-50050d8ab2d5` を使用し、`docs/*.md` 14件がすべて `ready` であることを確認した。
- `python scripts/sync_docs_to_notebooklm.py` を再実行し、AIエージェント向け `exports/knowledge_flow/notebooklm_agent_brief.md/json` と、社長向け `exports/knowledge_flow/notebooklm_ceo_slide_outline.md/json` を生成した。
- `scripts/upload_notebooklm_docs_to_drive.py` のGoogle Docs化対象にAgent BriefとCEO Slide Outlineを追加した。
- WBSは `T643`, `T650`, `T651` を完了へ更新し、`T656`, `T657` を追加した。

検証:

- `python -m compileall src scripts` 成功。
- `notebooklm status` と `notebooklm source list --json` で、notebookおよび14 sources readyを確認。
- Google Sheets へ `73 source rows` / `85 hierarchical WBS display rows` を同期済み。
- Google Calendarへ `NotebookLM補助ログイン導線作成` と `NotebookLM CEO Slide Outline取得` を追加し、既存重複イベントも削除済み。最終結果は `Success: 24, Updated: 24, Failed: 0`。
- GitHub Issues #7, #9, #10 は成果物リンク付きでクローズ済み。

## 2026-05-22 NotebookLM PPTX化・連携証跡更新

実施内容:

- `scripts/generate_ceo_presentation_deck.py` を追加し、NotebookLM CLIで取得したCEO Slide Outlineを社長説明用PowerPointへ変換した。
- 生成成果物は `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx`、サマリーは `.md`、生成manifestは `.json` に保存した。
- `python-pptx>=1.0.2` を `requirements.txt` に追加した。
- `scripts/upload_notebooklm_docs_to_drive.py` を更新し、Google Docs化したNotebookLM資料に加えてPPTXファイルもDriveへアップロードできるようにした。
- Slack CLIは未検出、Slack送信MCPは未露出、GitHub Projectは `read:project` 不足であることを再確認した。
- Notion MCPでPPTX証跡ページ `https://www.notion.so/3671d736b9db81d3ac3cc7a716699c37` を作成した。
- WBSに `T658` から `T663` を追加し、Calendar同期対象にもPowerPoint化・Drive共有・Notion証跡・Project再追跡・最終パックレビューを追加した。

検証:

- `python scripts/generate_ceo_presentation_deck.py` 成功。PPTX package内のslide数は8枚。
- `notebooklm status` / `notebooklm source list --json` で既存Notebookと14 sources readyを確認。
- `gh project list --owner kanta13jp1 --format json` は `read:project` scope不足で失敗。Issue #8/#5で継続管理。
- Google Sheetsへ `79 source rows` / `91 hierarchical WBS display rows` を再同期済み。
- Google Calendarへ新規4イベントを含む `Success: 28, Updated: 24, Failed: 0` を再同期済み。

## 2026-05-22 Claude Code レーン追加 (3-tool 体制移行)

これまでは Antigravity + Gemini / VSCode + Codex の 2-tool 体制だったが、本日 (2026-05-22) より **VSCode + Claude Code** を第 3 レーンとして正式化した。役割と handoff 規約は [docs/MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) に集約。

### Codex から見た Claude Code レーンの境界

- **Claude Code が触る**: `docs/*.md` の architect 系 / checklist / risk register / PR review / WBS 状態調停 (Sheets ↔ Issues ↔ Notes の不整合検出)
- **Claude Code が触らない**:
  - `data/WBS.tsv` (Codex のみ書き込み — 既存規約維持)
  - `scripts/*.py` の実装 (Codex 領分)
  - `src/*` の実装 (Codex / Antigravity)
  - Gemini API の直接呼び出し
- **handoff コミット prefix**: Claude Code は `[claude]`、Codex は `[codex]` をコミットメッセージ先頭に付ける。
- **PR ラベル**: `tool:claude` / `tool:codex` で起票元を明示。
- **マージ順**: `[codex] PR → [claude] review → main → [antigravity] rebase`。Antigravity-first 禁止。

### 5/27 18:48 quota refresh 切り戻し時の Codex の役割

quota 復帰後は Antigravity が frontend / マルチモーダル / Pro 推論を取り戻す。Codex は backend / sync / CI / gh CLI に専念する。切り戻しの handoff note は Claude Code が本ファイルに「YYYY-MM-DD quota 復帰 切り戻し」セクションを追加する形で発行する予定。

### 本日 Claude Code が起票した docs

- 新規 [docs/MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) — 3-tool 構成、handoff 規約、6/2 day-by-day、Best Practices Refresh (2026-05-22)
- 新規 [docs/CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md](CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md) — T663 deliverable (35 項目 7 セクション)
- 新規 [docs/CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) — **T605 完遂** (17 論点 D/C/O/X)
- [docs/ANTIGRAVITY_GUIDE.md](ANTIGRAVITY_GUIDE.md) に MULTI_AI_WORKFLOW への cross-link 追記
- [docs/CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) に「Risks & Blockers」表 (R1-R8) と DISCUSSION_POINTS / FINAL_REVIEW_CHECKLIST / MULTI_AI_WORKFLOW への link を追加
- [README.md](../README.md) Documents セクションに MULTI_AI_WORKFLOW / ANTIGRAVITY_GUIDE / FINAL_REVIEW_CHECKLIST / DISCUSSION_POINTS を追加

### Codex への handoff キュー (WBS.tsv 反映依頼)

Claude Code レーンは `data/WBS.tsv` を直接編集しない規約のため、以下の status flip を Codex セッションでお願いしたい:

- **T605** ステータス `未着手` → `完了`、終了予定日 `2026-05-28` → 実際終了日 `2026-05-22`、実行エンジン `VSCode + Codex` → `VSCode + Claude Code`、担当 `人間 + Codex` → `Claude Code` (3-tool 体制移行に伴う lane 再割り当て)
- 同時に WBS の `T663` を `未着手` → `実行中` に更新可 (Final Review checklist の framework が docs/CEO_PRESENTATION_FINAL_REVIEW_CHECKLIST.md として整備済のため、本格 review 期間 5/30-6/1 まで `実行中` 扱い妥当)

### Codex への best practice 採用候補キュー ([MULTI_AI_WORKFLOW Best Practices Refresh](MULTI_AI_WORKFLOW.md#best-practices-refresh-2026-05-22) 参照)

- [x] レポジトリルートに `AGENTS.md` 新規作成 (Codex 用 review behavior + WBS/同期/公開URL guard規約) — T664で完了
- [ ] `.codex/config.toml` で `model` / `sandbox_mode` / `approval_policy` を固定
- [ ] `scripts/sync_docs_to_notebooklm.py` に Gemini explicit context caching (1-hour TTL) を導入
- [ ] Codex skills packaging: `/sync-wbs`, `/sync-notebooklm`, `/verify-demo`
- [ ] 5/27 Antigravity 復帰後に Antigravity CLI 評価 (旧 Gemini CLI からの移行)

### R1 リスク降格提案

[docs/CEO_PRESENTATION_PREP_2026-06-02.md Risks & Blockers](CEO_PRESENTATION_PREP_2026-06-02.md#risks--blockers-2026-05-22-時点) の **R1 (Gemini 3.5 Pro 来月待ち) を HIGH → MED に降格**することを Codex レーンに提案。根拠: I/O 2026 公式ベンチで **Gemini 3.5 Flash が 3.1 Pro を 4 倍速で上回る** ことが公表されたため、Pro 公開待ちは 6/2 デモのブロッカーではない。サービス方向性 pack ([DECISION_PACK 判断マトリクス](CEO_PRESENTATION_DECISION_PACK_2026-06-02.md#判断マトリクス)) は Flash 品質で出荷可能。

## 2026-05-22 (2nd session) Claude Code WBS 完遂: T607 想定QA

本日 2 回目の Claude Code セッションで **T607 (想定 QA + 保留時の対応)** を完遂。WBS 上の予定は 5/29-5/30 → 1 週間前倒し。

### 完遂内容

- 新規 [docs/CEO_PRESENTATION_QA_PACK_2026-06-02.md](CEO_PRESENTATION_QA_PACK_2026-06-02.md) — 22 QA を 6 カテゴリ (サービス方向性 / 技術 / 運用 / リスク / 連携 / ロードマップ) で構造化。各 QA に「回答方針」「保留時の対応」「関連論点番号 (T605 の D/C/O/X)」を付与。
- 保留フロー (即答できない質問のハンドリング) + 当日機材チェックリスト 9 項目を含む。
- [docs/CEO_PRESENTATION_PREP_2026-06-02.md 想定質問と回答方針](CEO_PRESENTATION_PREP_2026-06-02.md) に QA_PACK へのリンクを追加 (既存 6 行表は simplified 版として温存)。
- [README.md](../README.md) Documents セクションに QA_PACK 追加。
- [docs/CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) ヘッダの関連 docs リンクに QA_PACK 追加。

### WBS.tsv 反映依頼 (Codex セッションへ handoff)

- **T607** ステータス `未着手` → `完了`、終了予定日 `2026-05-30` → 実際終了日 `2026-05-22`、実行エンジン `VSCode + Codex` → `VSCode + Claude Code`、担当 `Codex` → `Claude Code` (3-tool 体制移行に伴う lane 再割り当て)

### Best Practices Refresh delta (light 2nd pass)

[MULTI_AI_WORKFLOW.md Light refresh セクション](MULTI_AI_WORKFLOW.md#light-refresh-2026-05-22-2nd-pass--24h-以内差分のみ) に追記済。要点:

- **Anthropic Claude Code**: Rewind menu "Summarize up to here" で 1M context 圧縮可能、`/resume` で background session 復帰可能 ([Changelog](https://code.claude.com/docs/en/changelog))。
- **Google Antigravity 2.0** (前回未捕捉): **JSON hooks** + **live voice transcription** が公式機能化 ([Google Developer Blog](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/))。JSON hooks は sync スクリプト群 (Codex レーン) の自動起動 trigger 候補、live voice transcription は 6/2 デモのリアルタイム議事録化候補。
- **OpenAI Codex**: 24h 以内のため変更なし、0.133.0 維持。

### Codex への handoff キュー追加分

既存 5 件 (AGENTS.md / .codex/config.toml / context caching / skills / Antigravity CLI 評価) に加えて:

- [ ] [docs/CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md](CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md) の markdownlint MD032 (blanks-around-lists) 13 件を一括修正 (Claude Code が初版作成時に発生、blank line 構造の整え)
- [ ] [docs/CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md) 既存コンテンツ 285-422 行の MD034 (bare URLs) 9 件を一括修正
- [ ] [Antigravity 2.0 JSON hooks](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/) を sync スクリプト群の trigger に利用できるか PoC (5/27 Antigravity 復帰後)
- [ ] Antigravity 2.0 live voice transcription を 6/2 デモ T640 リハーサルで評価

## 2026-05-22 (3rd session) Claude Code WBS 完遂: T606 + tracker tabs インフラ

本日 3 回目の Claude Code セッションで **T606 (運用・体制・リスク・費用感 論点)** を完遂。WBS 上の予定は 5/28-5/29 → 1 週間前倒し。加えてユーザーからの新規 3 ルール (commit/push/merge / Sheets+Calendar sync / 課題管理表+QA表) に対応するインフラを起票。

### 3rd session 完遂内容

- 新規 [docs/CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md](CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md) — 12 Q-OPS + 5 新規リスク (R9-R13) + 方向性別費用感 (T606 deliverable)
- 新規 [docs/SHEETS_TRACKERS_SCHEMA.md](SHEETS_TRACKERS_SCHEMA.md) — Sheets 追加 2 タブ (課題管理表 / QA表) のカラム定義 + sync スクリプト実装方針 + 運用フロー
- 新規 [data/issues_tracker.tsv](../data/issues_tracker.tsv) — 24 行 (R1-R13 既存リスク + HANDOFF-1..11 Codex キュー)
- 新規 [data/qa_tracker.tsv](../data/qa_tracker.tsv) — 34 行 (QA-01..22 from QA_PACK + Q-OPS-01..12 from OPS_DISCUSSION)
- [docs/CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) 関連 docs リストに OPS_DISCUSSION + SHEETS_TRACKERS_SCHEMA 追加
- [README.md](../README.md) Documents セクションに OPS_DISCUSSION + SHEETS_TRACKERS_SCHEMA 追加

### 3rd session WBS.tsv 反映依頼 (Codex セッションへ handoff)

- **T606** ステータス `未着手` → `完了`、終了予定日 `2026-05-29` → 実際終了日 `2026-05-22`、実行エンジン `VSCode + Codex` → `VSCode + Claude Code`、担当 `人間 + Codex` → `Claude Code`

### 3rd session Codex への handoff キュー追加 (sync スクリプト実装が最優先)

- [x] **HANDOFF-10** `課題管理表` 同期 — `sync_wbs_to_sheets.py` に統合済み。`data/issues_tracker.tsv` → Sheets `課題管理表` タブ。スキーマ [SHEETS_TRACKERS_SCHEMA.md](SHEETS_TRACKERS_SCHEMA.md) §1
- [x] **HANDOFF-11** `QA表` 同期 — `sync_wbs_to_sheets.py` に統合済み。`data/qa_tracker.tsv` → Sheets `QA表` タブ。スキーマ [SHEETS_TRACKERS_SCHEMA.md](SHEETS_TRACKERS_SCHEMA.md) §2
- [x] 既存 `sync_wbs_to_sheets.py` の `worksheet.clear()` が `課題管理表` / `QA表` タブを破壊しないことを確認 (保護対象タブIDに追加)

### 新 3 ルール対応の Codex 側アクション

1. [feedback-session-commit-push-merge](../.claude/projects/c--Users-kanta-GitHub-mighty-link-ai-connect/memory/feedback_session_commit_push_merge.md) (memory) — Codex セッションも同様の commit/push/PR/merge フローを厳守。`[codex]` prefix で main へ短サイクル merge。
2. [feedback-session-sheets-calendar-sync](../.claude/projects/c--Users-kanta-GitHub-mighty-link-ai-connect/memory/feedback_session_sheets_calendar_sync.md) (memory) — Codex セッション末でも `sync_wbs_to_sheets.py` + `sync_wbs_to_calendar.py` (+ 新規 2 sync スクリプト実装後はそれらも) を実行。
3. [feedback-session-sheets-trackers](../.claude/projects/c--Users-kanta-GitHub-mighty-link-ai-connect/memory/feedback_session_sheets_trackers.md) (memory) — Codex が `data/issues_tracker.tsv` / `data/qa_tracker.tsv` を直接書き込む場合は事前に Claude Code に PR コメントで通知 (排他規約反転防止)。

## 2026-05-22 Codex continuation: T664 三ツール開発フロー整備

Gemini quota中でも開発を止めないため、Antigravity + Gemini / VSCode + Codex / VSCode + Claude Code の三ツール運用を共有手順へ固定した。

### 完了内容

- 新規 `AGENTS.md`: Codex / multi-agent 共通のセッションゲートを定義。
- 新規 `CLAUDE.md`: Claude Code project memory entrypointとして `@AGENTS.md` を import。
- `.gitignore`: `.claude/settings.local.json` と `CLAUDE.local.md` をローカル専用として除外。
- `scripts/sync_wbs_to_sheets.py`: WBS 3タブに加え、`data/issues_tracker.tsv` → `課題管理表`、`data/qa_tracker.tsv` → `QA表` を同一OAuth実行で同期するよう拡張。
- `data/issues_tracker.tsv`: HANDOFF-2 / HANDOFF-10 / HANDOFF-11 を resolved 化。
- `data/qa_tracker.tsv`: 公式Docs確認ルールの実問QA `Q-AHOC-20260522-1` を追加。
- `data/WBS.tsv` / `docs/WBS.md`: T664を追加し完了。
- `scripts/sync_wbs_to_calendar.py`: T664カレンダーイベントを追加。
- GitHub Issue #13を作成し、T664完了証跡としてクローズ。

### 採用した公式Docs由来の運用

- Anthropic: Claude Codeは `CLAUDE.md` を project memory として読むため、共通ルールは `CLAUDE.md` から `@AGENTS.md` importで共有。
- OpenAI: Codexはrepo rootの `AGENTS.md` をプロジェクト指示として読むため、WBS/同期/公開URL guardを同ファイルに固定。
- Google: Sheets APIのbatchUpdate思想に合わせ、書式処理とtrackerタブ装飾をまとめて実行し、API呼び出しを抑制。

### 残課題

- GitHub Projectは引き続き `read:project` scope不足。`gh auth refresh -h github.com -s read:project -s project` 後にT645を再開。
- SlackはCLI/送信MCP未露出のため、T653で投稿先・権限確認後に再開。

## 2026-05-22 (4th session) Claude Code WBS 完遂: T615 + stale-doc 削除ルール導入

本日 4 回目の Claude Code セッションで **T615 (決定後ロードマップ枠)** を完遂。WBS 上の予定は 6/1-6/2 → 10 日以上前倒し。加えてユーザーからの新規ルール「内容が古いドキュメントはどんどん削除してください」に対応するメモリ追加と最初の stale-doc 訂正を実施。

### 4th session 完遂内容

- 新規 [docs/CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md](CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md) — 方向性 A/B/C/D 別 Phase 7 WBS テンプレ + 共通 Phase 7-common (T701-T708) + 議事録 → WBS 反映 7 ステップ手順 (T615 deliverable)
- [docs/ANTIGRAVITY_GUIDE.md](ANTIGRAVITY_GUIDE.md) 表中の **Gemini 3.5 Pro「来月予約」表現を訂正** — I/O 2026 公表ベンチで Gemini 3.5 Flash > 3.1 Pro at 4x speed が確定したため。R1 リスクを `LOW / resolved` に降格。
- [docs/MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) に Best Practices Refresh 4th pass (no changes) と stale-doc 訂正ログを追記。
- [docs/CEO_PRESENTATION_PREP_2026-06-02.md](CEO_PRESENTATION_PREP_2026-06-02.md) 関連 docs リストに POST_DECISION_ROADMAP 追加。
- [README.md](../README.md) Documents セクションに POST_DECISION_ROADMAP 追加。
- [data/issues_tracker.tsv](../data/issues_tracker.tsv) — R1 `MED/in_progress → LOW/resolved`、HANDOFF-12 新規追加 (Phase 7 採用後の本書 stale セクション削除計画)。
- 新規 memory: `feedback_stale_doc_deletion.md` — 古い記述を append-only ではなく能動的に削除する運用ルール。

### 4th session WBS.tsv 反映依頼 (Codex セッションへ handoff)

- **T615** ステータス `未着手` → `完了`、終了予定日 `2026-06-02` → 実際終了日 `2026-05-22`、実行エンジン `VSCode + Codex` → `VSCode + Claude Code`、担当 `Codex` → `Claude Code`
- 既存依頼 (T605/T606/T607 の `完了` flip と T663 の `実行中` 化) と一括 commit 推奨

### 4th session Codex への handoff キュー追加

- **HANDOFF-12** Phase 7 採用後の POST_DECISION_ROADMAP 不要セクション物理削除 (6/3 までに方向性確定後に実行) — [[feedback-stale-doc-deletion]] 準拠
- 既存 HANDOFF-3〜9 はそのまま (5/27 quota refresh 後対応分含む)

### 採用した stale-doc 削除ルール

[[feedback-stale-doc-deletion]] memory を新規追加。今回の対応:

- ANTIGRAVITY_GUIDE.md の Gemini Pro 来月予約表現を訂正 (削除ではなく上書き)
- POST_DECISION_ROADMAP.md は 6/2 後に方向性確定で不要セクションを削除する計画を HANDOFF-12 として事前に登録
