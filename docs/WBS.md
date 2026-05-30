# 📊 Mighty-Link AI Connect: プロジェクトWBS (作業分解構成図)

> [!NOTE]
> **本WBSの設計思想**
> 開発するプロダクト **『Mighty Skill-Bridge（エンジニア＆案件 AIフィットシミュレーター）』** を、Antigravity 2.0 およびGoogle Gemini APIの現行モデルを用いて開発するための完全詳細タスクリストです。
> 最新の **Google Workspace API (Sheets/Docs/Calendar) ＆ Gemini API 連携** の思想に基づき、スプレッドシートにコピペするだけで即座に動的なプロジェクト管理ボードとして機能するフォーマットで設計されています。

---

## 📅 WBS フェーズ別サマリー

```mermaid
gantt
    title Mighty Skill-Bridge 開発スケジュール
    dateFormat  YYYY-MM-DD
    section フェーズ1: 企画・設計
    要件定義 & DB設計          :active, a1, 2026-05-20, 2d
    section フェーズ2: フロントエンド開発
    UIコンポーネント実装        : b1, after a1, 3d
    section フェーズ3: バックエンド & AI
    Gemini API 連携 : c1, after b1, 3d
    section フェーズ4: テスト & デバッグ
    Browser Agent & Code Mender: d1, after c1, 2d
    section フェーズ5: 本番公開
    CI/CDデプロイ & プレスリリース: e1, after d1, 2d
    section フェーズ6: 社長プレゼン準備
    6/2判断材料・デモ・連携フロー準備: f1, 2026-05-21, 13d
```

---

## 📑 WBS 詳細テーブル

*※この表は、`data/WBS.tsv` ファイルからスプレッドシートにコピペするだけで、全く同じレイアウトでスプレッドシート上に再現されます。*

| タスクID | 大フェーズ | 小フェーズ | タスク名 | 担当 | 実行エンジン | Sheets Live 連携アクション |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T101** | 1. 企画・設計 | 要件定義 | `requirements.md` の策定 | 人間 + AI | Gemini API 現行モデル | 完了時に Docs Live へ自動文書書き出し |
| **T102** | 1. 企画・設計 | DB設計 | `database.md` とスキーマ設計 | AIエージェント | Gemini API 現行モデル | テーブル定義をスプレッドシートへ自動同期 |
| **T201** | 2. フロント開発 | UI/UX実装 | PDF/画像ドラッグ＆ドロップ画面 | AIエージェント | Antigravity 2.0 | 実装進捗を Sheets Live にリアルタイム反映 |
| **T202** | 2. フロント開発 | UI/UX実装 | フィット分析結果（レーダーチャート等） | AIエージェント | Antigravity 2.0 | UIコンポーネントのテスト結果をセルへ記録 |
| **T301** | 3. バックエンド | API開発 | ファイルアップロード＆パースAPI | AIエージェント | Gemini API 現行モデル | API仕様書を Docs Live に自動同期 |
| **T302** | 3. バックエンド | AIコア連携 | Gemini API マルチモーダル解析 | AIエージェント | Gemini API 現行マルチモーダルモデル | プロンプト応答ログを Sheets Live に蓄積 |
| **T303** | 3. バックエンド | 提案生成 | 面談想定質問＆育成ロードマップ生成 | AIエージェント | Gemini API 現行モデル | 生成結果のフォーマットを Sheets 側で管理 |
| **T304** | 3. バックエンド | AI基盤肉付け | 構造化プロファイル抽出・4軸スコアリングfallback実装 | Codex | VSCode + Codex | AI復帰時に渡す structured_profile / gap_analysis を Sheets ログへ拡張可能にする |
| **T305** | 3. バックエンド | AI監査基盤 | AI判定監査ログ(JSONL)・recent audit API実装 | Codex | VSCode + Codex | AI評価根拠・matched/missing skills をローカル監査ログへ蓄積し復帰後の改善に利用 |
| **T306** | 3. バックエンド | 公開デモ保護 | GitHub Pages root index ガード・CI検証 | Codex | VSCode + Codex | 社長共有済み公開URLのREADME fallbackを防止し、push前後のUIマーカー検証を必須化 |
| **T307** | 3. バックエンド | WBS可視化強化 | CATS型WBSスプレッドシートUI・集計/タイムラインタブ実装 | Codex | VSCode + Codex | 参照WBSに近い階層・進捗・予定/実績・集計ビューをSheetsへ自動生成 |
| **T401** | 4. 検証・品質 | テスト実行 | Browser Agent による自律UI/UXテスト | AIエージェント | Browser Agent | テスト合格率・バグ率を Sheets Live にプロット |
| **T402** | 4. 検証・品質 | セキュリティ | Code Mender による脆弱性自動修正 | AIエージェント | Code Mender | 脆弱性修復ログを Sheets セキュリティタブに同期 |
| **T501** | 5. デプロイ | インフラ | CI/CD（GitHub Actions）設定 | AIエージェント | Gemini API 現行モデル | デプロイ成否・本番URLを Sheets に自動書き込み |
| **T502** | 5. デプロイ | リリース | プレスリリース・SNS告知文の自動生成 | 人間 + AI | Gemini API 現行モデル | 告知文候補（3パターン）を Docs Live に書き出し |
| **T601** | 6. 社長プレゼン準備 | 方針整理 | 6/2打ち合わせの目的・決定事項・判断軸整理 | Codex | VSCode + Codex | プレゼン準備ブリーフをDocs/Sheetsへ同期できる形で整備 |
| **T602** | 6. 社長プレゼン準備 | デモ構成 | 公開URLデモの見せ方・説明順・想定操作シナリオ設計 | Codex | VSCode + Codex | デモシナリオと確認観点をWBS Summaryへ反映 |
| **T603** | 6. 社長プレゼン準備 | 安定稼働確認 | 公開URL・ローカルAPI・Google Sheets同期の本番前ヘルスチェック | Codex | VSCode + Codex | Public Demo Guardと同期結果を作業ログへ記録 |
| **T604** | 6. 社長プレゼン準備 | 資料骨子 | 社長向けプレゼン構成・スライド見出し・説明順の作成 | Codex | VSCode + Codex | 決定前提ではなく判断材料としてプレゼン骨子を管理 |
| **T605** | 6. 社長プレゼン準備 | 選択肢整理 | サービス内容決定前の論点・選択肢・確認質問リスト化 | Claude Code | VSCode + Claude Code | `CEO_PRESENTATION_DISCUSSION_POINTS_2026-06-02.md` へ6/2で決める論点・未決事項を整理済 |
| **T606** | 6. 社長プレゼン準備 | 運用・体制論点 | 6/2以降の開発体制・運用・リスク・費用感の論点整理 | Claude Code | VSCode + Claude Code | `CEO_PRESENTATION_OPS_DISCUSSION_2026-06-02.md` へ社長確認が必要な運用論点を整理済 |
| **T607** | 6. 社長プレゼン準備 | 想定QA | 社長からの想定質問・回答方針・保留時の対応整理 | Claude Code | VSCode + Claude Code | `CEO_PRESENTATION_QA_PACK_2026-06-02.md` へ想定QAと保留時対応を整理済 |
| **T608** | 6. 社長プレゼン準備 | 最終リハーサル | 公開デモ・WBS・説明資料の最終確認とバックアップ準備 | 人間 + Codex | VSCode + Codex | 最終チェック結果とバックアップURL/手順を記録 |
| **T609** | 6. 社長プレゼン準備 | 決定事項反映準備 | 6/2打ち合わせ後の決定事項・次期WBS反映テンプレート作成 | Codex | VSCode + Codex | 議事録後すぐWBS/Calendarへ反映できる更新枠を準備 |
| **T610** | 6. 社長プレゼン準備 | スライド化素材 | 1枚絵サマリー・デモ導線・判断ポイントのスライド素材整理 | Codex | VSCode + Codex | プレゼン当日の説明順をDocs化し、未確定内容は選択肢として明記 |
| **T611** | 6. 社長プレゼン準備 | 判断マトリクス | サービス方向性・対象ユーザー・優先機能の判断マトリクス作成 | Codex | VSCode + Codex | 6/2で決める選択肢を比較表として整理 |
| **T612** | 6. 社長プレゼン準備 | 議事録テンプレート | 決定事項・保留事項・次アクション記録テンプレート作成 | Codex | VSCode + Codex | 打ち合わせ直後にWBS/Calendar/Gitへ反映できる議事録枠を準備 |
| **T613** | 6. 社長プレゼン準備 | デモバックアップ | 公開URL障害時のローカル実行・スクリーンショット代替手順整理 | Codex | VSCode + Codex | Public Demo Guard結果と代替導線を本番前チェックリストへ反映 |
| **T614** | 6. 社長プレゼン準備 | 事前送付メモ | 社長へ事前共有する確認ポイント・当日アジェンダ短文作成 | Claude Code | VSCode + Claude Code | `CEO_PRESENTATION_PRESHARE_MEMO_2026-06-02.md` へ長文版・短文版・当日アジェンダ短文を整理済 |
| **T615** | 6. 社長プレゼン準備 | 決定後ロードマップ枠 | 6/2決定内容別の次期WBS更新パターン準備 | Claude Code | VSCode + Claude Code | `CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md` へ方向性別の次期WBS更新パターンを準備済 |
| **T616** | 6. 社長プレゼン準備 | 開発フロー設計 | NotebookLM・Slack・Notion・Obsidian連携の役割分担整理 | Codex | VSCode + Codex | 連携方針を作業手順書へ反映し、6/2の判断材料としてSheetsへ可視化 |
| **T617** | 6. 社長プレゼン準備 | NotebookLM連携 | 社長説明用のNotebookLM投入資料パックと利用シーン整理 | Codex | VSCode + Codex | Google Docs/Drive資料を読み解く候補フローとして判断パックへ反映 |
| **T618** | 6. 社長プレゼン準備 | Slack連携 | 進捗通知・レビュー依頼・決定ログ共有のSlack運用設計 | Codex | VSCode + Codex | 通知先・投稿タイミング・社長確認が必要なメッセージ種別を整理 |
| **T619** | 6. 社長プレゼン準備 | Notion連携 | 仕様・議事録・意思決定DB・バックログ管理のNotion運用設計 | Codex | VSCode + Codex | 決定事項とタスクをNotion DB化する候補として比較表へ反映 |
| **T620** | 6. 社長プレゼン準備 | Obsidian連携 | ローカルナレッジ・ADR・プロンプト資産のObsidian運用設計 | Codex | VSCode + Codex | 個人/開発メモと公式ドキュメントの境界を整理 |
| **T621** | 6. 社長プレゼン準備 | 連携デモ導線 | 4ツール連携を社長へ見せる説明順・画面遷移・価値訴求整理 | Codex | VSCode + Codex | 連携フローを確定機能ではなく判断材料としてプレゼン構成へ追加 |
| **T622** | 6. 社長プレゼン準備 | 権限・情報管理 | NotebookLM/Slack/Notion/Obsidian利用時の権限・機密情報ルール整理 | 人間 + Codex | VSCode + Codex | 外部共有可否・個人情報・認証情報の扱いを社長確認項目へ追加 |
| **T623** | 6. 社長プレゼン準備 | 連携採用判断 | 6/2で決める連携ツール優先順位・導入範囲・責任分担の確認リスト作成 | 人間 + Codex | VSCode + Codex | 採用/保留/後回しを決めるチェックリストを判断材料パックへ反映 |
| **T624** | 6. 社長プレゼン準備 | 連携成果物生成 | NotebookLM/Slack/Notion/Obsidianデモ成果物生成スクリプト実装 | Codex | VSCode + Codex | exports/knowledge_flow配下へ社長説明用ファイルを自動生成 |
| **T625** | 6. 社長プレゼン準備 | NotebookLM実体化 | NotebookLM投入用Source Pack生成と想定質問セット作成 | Codex | VSCode + Codex | notebooklm_source_pack.mdを生成し、社長説明前のQA作成に使える状態にする |
| **T626** | 6. 社長プレゼン準備 | Slack実体化 | 社長レビュー向けSlack進捗投稿案の生成 | Codex | VSCode + Codex | slack_ceo_update.mdとして投稿前確認できる文面を生成 |
| **T627** | 6. 社長プレゼン準備 | Notion実体化 | Notion用意思決定DB・バックログCSVの生成 | Codex | VSCode + Codex | notion_decision_log.csvとnotion_backlog_import.csvを生成 |
| **T628** | 6. 社長プレゼン準備 | Obsidian実体化 | Obsidian vault雛形・ADR・議事録・プロンプトノート生成 | Codex | VSCode + Codex | obsidian_vault配下にローカル知識ベースを作成 |
| **T629** | 6. 社長プレゼン準備 | 連携UIデモ | 公開デモ/ローカルUIへ開発ナレッジ連携デモセクション追加 | Codex | VSCode + Codex | 社長に画面上で4ツール連携の成果物リンクを見せられる状態にする |
| **T630** | 6. 社長プレゼン準備 | 連携APIデモ | FastAPIにKnowledge Flow生成・状態確認APIを追加 | Codex | VSCode + Codex | /api/knowledge-flow/generateで成果物を再生成できるようにする |
| **T631** | 6. 社長プレゼン準備 | 連携成果物検証 | 生成成果物・公開URL・API・Sheets/Calendar同期の総合確認 | Codex | VSCode + Codex | 社長提示前にデモ導線と生成ファイルの存在を確認する |
| **T632** | 6. 社長プレゼン準備 | GitHub Issues連携 | GitHub Issuesに6/2社長デモ向け連携タスクを起票 | Codex | gh CLI | Issue #1-#11/#13/#14/#16を作成・更新し、NotebookLM/Slack/Notion/Obsidian/GitHub Project/WBS連携を追跡可能にする |
| **T633** | 6. 社長プレゼン準備 | GitHub Project連携 | GitHub Project board取得・配置のCLI権限確認 | Codex | gh CLI | `read:project` スコープ不足を確認し、Project復旧タスクをIssue #5として管理する |
| **T634** | 6. 社長プレゼン準備 | NotebookLM実連携 | NotebookLM投入用Source PackをGoogle Drive/Docsへアップロード | Codex | Local OAuth Drive API | TXTをGoogle Docs化し、<k-umezawa@ml-mightylink.com>所有のNotebookLM source候補としてURLを証跡化する |
| **T635** | 6. 社長プレゼン準備 | Notion実連携 | Notion MCPで社長デモ用の連携証跡ページを作成 | Codex | Notion MCP | Google Doc URL、GitHub Issues、Slack/Projectの到達点、6/2決定事項をNotionページへ記録する |
| **T636** | 6. 社長プレゼン準備 | Slack連携確認 | Slack CLI/MCPの利用可否と投稿先確認フローを整理 | Codex | Slack MCP/CLI確認 | Slack CLI未検出・送信ツール未露出のため、投稿案とIssue #2で投稿先確認を管理する |
| **T637** | 6. 社長プレゼン準備 | Obsidian実連携 | Obsidian vaultとして開ける設定ファイルを追加 | Codex | VSCode + Codex | `.obsidian` 設定を生成対象へ追加し、ローカルvaultの入口を明確化する |
| **T638** | 6. 社長プレゼン準備 | 連携証跡台帳 | CLI/MCP連携の実行結果を社長説明用ドキュメントへ集約 | Codex | VSCode + Codex | Drive Doc、Notionページ、GitHub Issues、Project権限課題、Slack到達点を作業手順書へ反映する |
| **T639** | 6. 社長プレゼン準備 | Issue-WBS運用 | GitHub IssuesとWBSの相互参照ルールを整�| **T669** | 6. 社長プレゼン準備 | Seedance API payload alignment | Update FastAPI Seedance adapter to use ModelArk content-task payload and expose provider 400 response detail for setup debugging | Codex | VSCode + Codex + FastAPI + BytePlus official docs | `/api/seedance/video-demo` now sends `content[{type,text}]`, `ratio`, `duration` by default; `SEEDANCE_PAYLOAD_STYLE=prompt_legacy` remains available for alternate endpoints |
| **T670** | 6. 社長プレゼン準備 | Seedance async result polling | Add result polling after ModelArk task creation so the demo waits for the generated video URL instead of immediately falling back | Codex | VSCode + Codex + FastAPI + BytePlus official docs | `SEEDANCE_RESULT_API_URL_TEMPLATE`, `SEEDANCE_POLL_TIMEOUT_SECONDS`, and `SEEDANCE_POLL_INTERVAL_SECONDS` control task result polling; health check now exposes polling readiness |
| **T671** | 6. 社長プレゼン準備 | Seedance browser-side task polling | Keep the returned Seedance `task_id` in the browser and continue polling until the generated video URL is ready | Codex | VSCode + Codex + FastAPI + browser DevTools evidence | `/api/seedance/video-task/{task_id}` checks an existing task once; `index.html` / `src/index.html` poll it every 10 seconds after pending responses |
| **T672** | 6. 社長プレゼン準備 | Seedance saved default and cost guard | Save the generated Seedance video as the default local demo asset, add a download button, and disable billing API calls unless explicitly enabled | Codex | VSCode + Codex + FastAPI + BytePlus Console evidence | `SEEDANCE_API_ENABLED` gates external calls; default MP4 is the generated Seedance result; UI download link points to the current video |
| **T673** | 6. 社長プレゼン準備 | External API guard dashboard | Add a local admin dashboard, usage ledger, and circuit breakers for external API billing safety | Codex | VSCode + Codex + FastAPI + Official docs | `/admin` and `/api/admin/usage` show daily calls, blocked calls, provider-reported tokens, saved Seedance video, and recent API events; Seedance daily generation limit defaults to 1 and API remains disabled unless explicitly enabled |
| **T674** | 6. 社長プレゼン準備 | Favicon and local route polish | Add a branded favicon and resolve browser 404/deprecation noise for local demo routes | Codex | VSCode + Codex + FastAPI + Pillow + Google GenAI SDK | Generated root `favicon.ico`, wired `/favicon.ico` for FastAPI and GitHub Pages, added `/admin/usage` alias, migrated Gemini import to `google-genai`, and applied a Windows selector loop policy to reduce local video-stream disconnect noise |
| **T675** | 6. 社長プレゼン準備 | Chrome DevTools workspace route | Add the Chrome DevTools automatic workspace JSON route to remove localhost 404 noise | Codex | VSCode + Codex + FastAPI + Chrome official docs | FastAPI now returns DevTools workspace JSON at `/.well-known/appspecific/com.chrome.devtools.json` with the local project root and a stable UUID so Chrome DevTools stops logging 404 for that development-only request |
| **T676** | 6. 社長プレゼン準備 | Seedance風ナビ/フッター刷新 | Seedance公式ページに近いヘッダー/フッター項目配置とスクロール時ヘッダー挙動を公開デモへ追加 | Codex | VSCode + Codex + Playwright + Official Docs | `index.html` / `src/index.html` を生成元から再描画し、Home / Models / Blog & Publication / Join Us、EN / JP、Models / Teams / Learn More系フッター、動画デフォルト / Download / Seedance API導線を維持してPC/モバイル検証を完了する |
| **T677** | 6. 社長プレゼン準備 | Sheetsガント風タイムライン化 | WBS Timelineタブを添付画像のように日付軸とバーで予定を可視化できる表示へ改善 | Codex | VSCode + Codex + Google Sheets API | `sync_wbs_to_sheets.py` で `data/WBS.tsv` から日別列、月ヘッダー、今日ライン、状態別バー、固定列を生成し、WBS/課題管理表/QA表と同時にGoogle Sheetsへ同期する |
| **T678** | 6. 社長プレゼン準備 | Sheets遅延タスク可視化 | WBS Timelineでスケジュール遅延・期限間近タスクを色で把握できるようにする | Codex | VSCode + Codex + Google Sheets API | `sync_wbs_to_sheets.py` のGantt表示へ遅延列、終了遅れ/着手遅れ/期限間近判定、行色、バー色、条件付き書式を追加し、Google Sheets API `batchUpdate` で同期する |
| **T679** | 6. 社長プレゼン準備 | UI・動画非同期化 | 縦統合型シネマティックダッシュボードへのリファクタリング（被らない動画＆非同期化） | AIエージェント | Antigravity + Gemini | `index.html` のデモ動画プレビューと入力フォームの重なりを解消し、最上部動画と下部動画の再生ソースを非同期化する |
| **T680** | 6. 社長プレゼン準備 | UI・動画リソース | 最上部動画のprocedural fallback固定と下部詳細プレイヤーのSeedance API動画割り当ての修正 | AIエージェント | Antigravity + Gemini | 最上部背景動画をprocedural fallbackに固定し、下部詳細動画とダウンロード用ソースにSeedance API製MP4を設定し、完全非同期化をビジュアル検証・修正する |
| **T681** | 6. 社長プレゼン準備 | UI・動画生成 | Seedance APIによる最上部ブランドループ動画の新規生成と静的差し替え | AIエージェント | Antigravity + Gemini | scripts/generate_seedance_brand_video.py を実装し、環境変数設定時に実APIにて美麗なデータネットワーク動画を生成してmighty_skill_bridge_procedural_fallback.mp4を完全に上書き静的配置する |
| **T682** | 6. 社長プレゼン準備 | Seedance UI刷新 | 極限のSeedance風UI再現と4言語（EN, 中文, KO, JP）スクロールアニメーション polish | AIエージェント | Antigravity + Gemini | WBS/Timeline/課題管理表/QA表と自動同期し、完了タスクのカレンダーイベントを削除 |
| **T683** | 6. 社長プレゼン準備 | Admin Dashboard Link | デモ画面から管理者ダッシュボード（/admin）へ直接遷移できるリンクをヘッダーとフッター（Learn More）に実装し、FastAPI/静的環境での親和性を高める | AIエージェント | Antigravity + Gemini | ヘッダーとフッターに/adminリンクを追加し、静的ホスティング（GitHub Pages）用にモックデータへ切り替わる admin/index.html を新設して404を解消 |
| **T684** | 6. 社長プレゼン準備 | インフラ | requirements.txt 依存ドリフトの監視・freeze | Claude+Codex | VSCode + Claude Code | dependencyのfreezeとupgrade禁止期間の運用監視 |
| **T685** | 7. 次期開発・運用 | コンプライアンス | 個人情報同意書テンプレート作成とクローズド運用設計 | 人間+Claude | VSCode + Claude Code | 社長承認後の同意書テンプレート整備と運用ルールの策定 |
| **T686** | 7. 次期開発・運用 | セキュリティ | デモ環境へのbasic authまたはIP制限の導入設計 | Codex | VSCode + Codex | 社長承認後のデモ環境認証/アクセス制限実装 |
| **T687** | 7. 次期開発・運用 | コスト | 3 AIツール並走時のquotaメーター監視と超過レポート設計 | Codex | VSCode + Codex | 社長承認後のコスト上限設定および優先laneポリシー決定 |
| **T688** | 6. 社長プレゼン準備 | コスト | Antigravity 2.0 Managed Agents料金・利用条件の確認と監視 | Codex+Claude | VSCode + Codex | 公式情報に基づくManaged Agents料金監視体制の整備 |
| **T689** | 7. 次期開発・運用 | インフラ | 3-tool体制開発手順書による属人性軽減と再現性確保 | Claude | VSCode + Claude Code | マルチAIワークフロー手順書の継続更新と属人性排除 |
| **T690** | 6. 社長プレゼン準備 | インフラ | Codexセッション設定のリポジトリレベル固定化(.codex/config.toml) | Codex | VSCode + Codex | 設定ファイルの適用によるセッションドリフト防止 |
| **T691** | 7. 次期開発・運用 | インフラ | NotebookLM同期スクリプトへのGemini explicit context caching導入検証 | Codex | VSCode + Codex | Google公式caching docsに沿ったTTL指定によるコスト削減PoC |
| **T692** | 7. 次期開発・運用 | インフラ | Codex skills機能による定型運用コマンド(3 skills)のリポジトリレベルパッケージ化 | Codex | VSCode + Codex | 1 job = 1 skill 規則に従った自動化パッケージ整備 |
| **T693** | 6. 社長プレゼン準備 | インフラ | Antigravity CLIの機能評価と動作検証 | Antigravity | Antigravity + Gemini | Google公式Docsに基づくCLI実機検証と可否判断 |
| **T694** | 6. 社長プレゼン準備 | ドキュメント | 主要docs内のmarkdownlint指摘事項(22件)の一括自動修正 | Codex | VSCode + Codex | markdownlint --fixによる構造不整合の一括解消 |
| **T695** | 7. 次期開発・運用 | 連携 | Antigravity hooks機能によるsyncスクリプト自動起動の可否検証 | Codex+Antigravity | VSCode + Codex | 自動化トリガーのPoCとマルチAI自動同期パイプライン整備 |
| **T696** | 7. 次期開発・運用 | インフラ | PPTX生成スクリプトへのCanvaインポート用ミニマルスタイル追加 | Codex | VSCode + Codex | --style canva-exportオプションによるCanva向け平滑PPTX生成 |
| **T697** | 7. 次期開発・運用 | インフラ | Playwrightによるデモ画面スクショ自動取得スクリプトの実装 | Codex | VSCode + Codex | 複数画面の定期自動キャプチャによるスライド素材作成自動化 |
| **T698** | 6. 社長プレゼン準備 | インフラ | Figma MCPを用いたワイヤーフレーム(10/20パターン)の自動流し込み | Claude Code | VSCode + Claude Code | Figma API/MCP連携によるワイヤーフレームフレーム一括構築 |

---

## 🤖 Sheets Live & Google Workspace API による自律同期シナリオ

Google Workspace API と `data/WBS.tsv` 正本運用を活かし、このWBSは以下のように同期・稼働します。

1. **リアルタイム進捗更新 (Sheets Live)**
   - Codex が各セッションで `data/WBS.tsv` を更新し、`sync_wbs_to_sheets.py` がGoogle Sheets APIを介してスプレッドシートの該当タスクの進捗ステータスと装飾を更新します。
2. **要件定義書のライブ同期 (Docs Live)**
   - 最初の要件定義（T101）で合意された `requirements.md` の内容は、Google Docs Live に自動で連携され、社長様とリアルタイムで共同編集・コメントのやり取りが可能な状態になります。
3. **24時間自律セキュリティレポート**
   - Code Mender（T402）が脆弱性を検出して自動でコードを修正すると、その安全レポートがスプレッドシート上の「セキュリティ・監査ログ」シートへ自律的に追加され、社長様に毎朝メールでダイジェストが届きます。��ゼン草案を取得して保存 | Codex | NotebookLM CLI + Local OAuth Drive API | NotebookLM notebook `75521ea6-6b9b-47b2-9508-50050d8ab2d5` の22 source ready状態からCEO Slide Outlineを取得し、Google Docs化対象に追加する |
| **T658** | 6. 社長プレゼン準備 | NotebookLM PowerPoint化 | NotebookLM CLIで取得したCEO Slide Outlineを社長説明用PowerPointへ変換 | Codex | NotebookLM CLI + python-pptx | `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02.pptx` を生成し、NotebookLM由来の構成を社長説明で開ける成果物にする |
| **T659** | 6. 社長プレゼン準備 | PowerPoint Drive共有 | 社長説明用PPTXを<k-umezawa@ml-mightylink.com>所有のGoogle Driveへアップロード | Codex | Local OAuth Drive API | `upload_notebooklm_docs_to_drive.py` でPPTXをDriveファイルとして登録し、NotebookLM資料と同じ証跡JSONへURLを記録する |
| **T660** | 6. 社長プレゼン準備 | Notion PPTX証跡更新 | Notion MCPでPPTX生成・Drive共有・残課題を証跡ページへ記録 | Codex | Notion MCP | PowerPoint成果物、NotebookLM notebook、Slack/Project制約、次アクションをNotionへ残す |
| **T661** | 6. 社長プレゼン準備 | GitHub Issues/Project再追跡 | PowerPoint生成タスクをGitHub Issuesへ追加し、Project権限不足を再確認 | Codex | gh CLI | PowerPoint成果物のIssueを起票・完了し、GitHub Projectはread:project不足としてIssue #8/#5で復旧待ちを継続する |
| **T662** | 6. 社長プレゼン準備 | Slack MCP/CLI到達性証跡 | Slack CLIと送信MCPの利用可否を確認し、投稿案と残課題を整理 | Codex | Slack MCP/CLI確認 | ローカルslack CLI未検出、送信MCP未露出を確認し、実送信は投稿先・権限確認後の残課題としてIssue #2/T653に集約する |
| **T663** | 6. 社長プレゼン準備 | 6/2資料最終パックレビュー | PPTX、NotebookLM資料、WBS、Calendar、Issue、Notion証跡を通しで確認 | 人間 + Codex | VSCode + Codex | 社長打ち合わせ前に公開URL・PPTX・Google Drive資料・WBS同期・残課題の見せ方を最終確認する |
| **T664** | 6. 社長プレゼン準備 | 三ツール開発フロー整備 | Antigravity + Gemini / VSCode + Codex / VSCode + Claude Codeの役割と毎セッション運用ルールを共有手順へ固定 | Codex | VSCode + Codex + Official Docs | 公式Docs確認、WBS 1件完了、Sheets課題管理表・QA表同期、commit/push/main/master反映までのセッションゲートをAGENTS.md/CLAUDE.md/手順書に反映する |
| **T665** | 6. 社長プレゼン準備 | 古いドキュメント削除・最新化 | 古いモデル前提・件数固定・Issue固定表記を削除/更新し、公式Docs確認ルールを強化 | Codex | VSCode + Codex + Official Docs | `ANTIGRAVITY_GUIDE.md` の未確認未来モデルセクションを削除し、NotebookLM 22 source / GitHub Issue #1-#11/#13/#14/#16/#18の現状へ更新する |
| **T666** | 6. 社長プレゼン準備 | Calendar完了イベント削除 | 完了済みWBSに紐づくGoogle Calendarイベントを削除し、未完了・実行中・会議イベントだけを残す同期ルールを実装 | Codex | VSCode + Codex + Google Calendar API | `sync_wbs_to_calendar.py` が `data/WBS.tsv` のステータスを読み、完了済みWBSイベントをCalendarからDELETEしてICS出力からも除外する |
| **T667** | 6. 社長プレゼン準備 | Seedance動画デモUI刷新 | 公開URLの第一画面を動画生成デモ中心のUIへ刷新し、既存デモ導線を維持する | Codex | VSCode + Codex + Playwright + Official Docs | `index.html` / `src/index.html` をMighty Skill-Bridgeの動画生成プレビューUIへ更新し、公開デモガードとローカル表示確認を完了する |
| **T668** | 6. 社長プレゼン準備 | Seedance API動画デモ接続 | FastAPIにSeedance API接続アダプタと静的動画フォールバックを追加し、公開URLで動画が表示される状態にする | Codex | VSCode + Codex + FastAPI + Playwright | `/api/seedance/video-demo`、`exports/seedance_demo`、`index.html` / `src/index.html` を接続し、`SEEDANCE_API_KEY` / `SEEDANCE_API_URL` 設定時に実APIへ切り替え可能にする |

---

## 🤖 Sheets Live & Google Workspace API による自律同期シナリオ

Google Workspace API と `data/WBS.tsv` 正本運用を活かし、このWBSは以下のように同期・稼働します。

1. **リアルタイム進捗更新 (Sheets Live)**
   - Codex が各セッションで `data/WBS.tsv` を更新し、`sync_wbs_to_sheets.py` がGoogle Sheets APIを介してスプレッドシートの該当タスクの進捗ステータスと装飾を更新します。
2. **要件定義書のライブ同期 (Docs Live)**
   - 最初の要件定義（T101）で合意された `requirements.md` の内容は、Google Docs Live に自動で連携され、社長様とリアルタイムで共同編集・コメントのやり取りが可能な状態になります。
3. **24時間自律セキュリティレポート**
   - Code Mender（T402）が脆弱性を検出して自動でコードを修正すると、その安全レポートがスプレッドシート上の「セキュリティ・監査ログ」シートへ自律的に追加され、社長様に毎朝メールでダイジェストが届きます。
| **T669** | 6. 社長プレゼン準備 | Seedance API payload alignment | Update FastAPI Seedance adapter to use ModelArk content-task payload and expose provider 400 response detail for setup debugging | Codex | VSCode + Codex + FastAPI + BytePlus official docs | `/api/seedance/video-demo` now sends `content[{type,text}]`, `ratio`, `duration` by default; `SEEDANCE_PAYLOAD_STYLE=prompt_legacy` remains available for alternate endpoints |
| **T670** | 6. 社長プレゼン準備 | Seedance async result polling | Add result polling after ModelArk task creation so the demo waits for the generated video URL instead of immediately falling back | Codex | VSCode + Codex + FastAPI + BytePlus official docs | `SEEDANCE_RESULT_API_URL_TEMPLATE`, `SEEDANCE_POLL_TIMEOUT_SECONDS`, and `SEEDANCE_POLL_INTERVAL_SECONDS` control task result polling; health check now exposes polling readiness |
| **T671** | 6. 社長プレゼン準備 | Seedance browser-side task polling | Keep the returned Seedance `task_id` in the browser and continue polling until the generated video URL is ready | Codex | VSCode + Codex + FastAPI + browser DevTools evidence | `/api/seedance/video-task/{task_id}` checks an existing task once; `index.html` / `src/index.html` poll it every 10 seconds after pending responses |
| **T672** | 6. 社長プレゼン準備 | Seedance saved default and cost guard | Save the generated Seedance video as the default local demo asset, add a download button, and disable billing API calls unless explicitly enabled | Codex | VSCode + Codex + FastAPI + BytePlus Console evidence | `SEEDANCE_API_ENABLED` gates external calls; default MP4 is the generated Seedance result; UI download link points to the current video |
| **T673** | 6. 社長プレゼン準備 | External API guard dashboard | Add a local admin dashboard, usage ledger, and circuit breakers for external API billing safety | Codex | VSCode + Codex + FastAPI + Official docs | `/admin` and `/api/admin/usage` show daily calls, blocked calls, provider-reported tokens, saved Seedance video, and recent API events; Seedance daily generation limit defaults to 1 and API remains disabled unless explicitly enabled |
| **T674** | 6. 社長プレゼン準備 | Favicon and local route polish | Add a branded favicon and resolve browser 404/deprecation noise for local demo routes | Codex | VSCode + Codex + FastAPI + Pillow + Google GenAI SDK | Generated root `favicon.ico`, wired `/favicon.ico` for FastAPI and GitHub Pages, added `/admin/usage` alias, migrated Gemini import to `google-genai`, and applied a Windows selector loop policy to reduce local video-stream disconnect noise |
| **T675** | 6. 社長プレゼン準備 | Chrome DevTools workspace route | Add the Chrome DevTools automatic workspace JSON route to remove localhost 404 noise | Codex | VSCode + Codex + FastAPI + Chrome official docs | FastAPI now returns DevTools workspace JSON at `/.well-known/appspecific/com.chrome.devtools.json` with the local project root and a stable UUID so Chrome DevTools stops logging 404 for that development-only request |
| **T676** | 6. 社長プレゼン準備 | Seedance風ナビ/フッター刷新 | Seedance公式ページに近いヘッダー/フッター項目配置とスクロール時ヘッダー挙動を公開デモへ追加 | Codex | VSCode + Codex + Playwright + Official Docs | `index.html` / `src/index.html` を生成元から再描画し、Home / Models / Blog & Publication / Join Us、EN / JP、Models / Teams / Learn More系フッター、動画デフォルト / Download / Seedance API導線を維持してPC/モバイル検証を完了する |
| **T677** | 6. 社長プレゼン準備 | Sheetsガント風タイムライン化 | WBS Timelineタブを添付画像のように日付軸とバーで予定を可視化できる表示へ改善 | Codex | VSCode + Codex + Google Sheets API | `sync_wbs_to_sheets.py` で `data/WBS.tsv` から日別列、月ヘッダー、今日ライン、状態別バー、固定列を生成し、WBS/課題管理表/QA表と同時にGoogle Sheetsへ同期する |
| **T678** | 6. 社長プレゼン準備 | Sheets遅延タスク可視化 | WBS Timelineでスケジュール遅延・期限間近タスクを色で把握できるようにする | Codex | VSCode + Codex + Google Sheets API | `sync_wbs_to_sheets.py` のGantt表示へ遅延列、終了遅れ/着手遅れ/期限間近判定、行色、バー色、条件付き書式を追加し、Google Sheets API `batchUpdate` で同期する |
| **T679** | 6. 社長プレゼン準備 | UI・動画非同期化 | 縦統合型シネマティックダッシュボードへのリファクタリング（被らない動画＆非同期化） | AIエージェント | Antigravity + Gemini | `index.html` のデモ動画プレビューと入力フォームの重なりを解消し、最上部動画と下部動画の再生ソースを非同期化する |
| **T680** | 6. 社長プレゼン準備 | UI・動画リソース | 最上部動画のprocedural fallback固定と下部詳細プレイヤーのSeedance API動画割り当ての修正 | AIエージェント | Antigravity + Gemini | 最上部背景動画をprocedural fallbackに固定し、下部詳細動画とダウンロード用ソースにSeedance API製MP4を設定し、完全非同期化をビジュアル検証・修正する |
| **T681** | 6. 社長プレゼン準備 | UI・動画生成 | Seedance APIによる最上部ブランドループ動画の新規生成と静的差し替え | AIエージェント | Antigravity + Gemini | scripts/generate_seedance_brand_video.py を実装し、環境変数設定時に実APIにて美麗なデータネットワーク動画を生成してmighty_skill_bridge_procedural_fallback.mp4を完全に上書き静的配置する |
| **T682** | 6. 社長プレゼン準備 | Seedance UI刷新 | 極限のSeedance風UI再現と4言語（EN, 中文, KO, JP）スクロールアニメーション polish | AIエージェント | Antigravity + Gemini | WBS/Timeline/課題管理表/QA表と自動同期し、完了タスクのカレンダーイベントを削除 |
| **T683** | 6. 社長プレゼン準備 | Admin Dashboard Link | デモ画面から管理者ダッシュボード（/admin）へ直接遷移できるリンクをヘッダーとフッター（Learn More）に実装し、FastAPI/静的環境での親和性を高める | AIエージェント | Antigravity + Gemini | ヘッダーとフッターに/adminリンクを追加し、静的ホスティング（GitHub Pages）用にモックデータへ切り替わる admin/index.html を新設して404を解消 |
