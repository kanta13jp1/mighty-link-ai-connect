# NotebookLM Agent Brief

Generated: 2026-05-22T21:50:26+09:00
Notebook: `75521ea6-6b9b-47b2-9508-50050d8ab2d5`

## Question

このNotebookに含まれる設計情報、作業手順、WBS、ロードマップをもとに、
Codex/AIエージェントが次に開発を進めるための要約を作ってください。

必ず以下を含めてください。
1. 現在のプロダクト方向性で確定していること
2. 6/2の社長打ち合わせまでに優先すべきプレゼン準備タスク
3. 6/2で社長に決めてもらうべき事項
4. バックエンド/app.pyやデータ構造を肉付けする時に守るべき前提
5. NotebookLM / Slack / Notion / Obsidian / GitHub Issues / GitHub Project の運用上の残課題
6. WBSへ追加すべき次アクション


## NotebookLM Answer

提供された最新の設計情報、作業手順、WBS、ロードマップ（3-tool開発体制、課題管理表・QA表の同期、stale-doc削除ルール、カレンダー完了イベント削除ルール、さらに新たに実装された「Seedance API動画デモの非同期ポーリング処理や課金ガード機能」など）に基づき、Codex / Claude Code / AntigravityによるAIエージェントが次に開発を進めるための要約を作成しました。

### 1. 現在のプロダクト方向性で確定していること
*   **コンセプトとプロトタイプの位置づけ**：「人と人、ビジネスとビジネス、そしてテクノロジーを“力強く繋ぐ”」というビジョンが確定しています[1]。実際の企画やサービス内容は6/2の社長打ち合わせまで決め打ちせず、現在のプロトタイプは意思決定のための「判断材料」として扱われます[2, 3]。
*   **実装済みの機能**：エンジニアの経歴書と案件票をGemini APIで解析し、4軸で評価するAIフィットシミュレーターが実装されています[4, 5]。UIは社長プレゼン向けに「Seedance API動画デモUI」へ刷新され[6, 7]、ModelArk Seedance向けのペイロード最適化（`content[{type,text}]` 形式のデフォルト化）や、動画生成の非同期タスクポーリング処理の実装が完了しています[8, 9]。また、WBS進捗やマッチング結果がGoogle Workspaceと自律的に連携する基盤を備えています[10]。
*   **開発体制とAI選定方針**：Antigravity+Gemini、VSCode+Codex、VSCode+Claude Codeの「**3-tool体制**」での並走開発が確定しています[11]。モデル名は固定せず、毎セッション開始時にAnthropic、OpenAI、Google、Microsoft、Meta、Amazon、Apple、Kimi、MiMo、DeepSeek、Grok、Seedance、Obsidian、Unityなど幅広い公式Docsの最新版を確認し、現行モデルから選定する方針です[12, 13]。

### 2. 6/2の社長打ち合わせまでに優先すべきプレゼン準備タスク
*   **ハードゲートのクリアとリハーサル (T663)**：5/30 EODまでに公開URLのデグレを防ぐ「Public Demo Guard」やデモ動画バックアップ等のハードゲートをクリアし、6/1にフルドライランを実施してデモ環境を凍結（`ceo-demo-2026-06-02`タグ作成）します[14-16]。
*   **判断材料の整備**：サービス方向性の判断マトリクス、17件の論点リスト、22件の想定QAパック、運用・費用感シナリオ、3種類の事前共有メモ（長文・短文・アジェンダ短文）など、意思決定を助けるプレゼン用パックを準備します[17-19]。
*   **ナレッジ連携のデモ準備**：機密情報を出さない範囲で、NotebookLM投入用資料、Slack投稿案、Notion向けCSV、Obsidianのvault雛形をローカル生成し、「実際に連携した状態」として提示できるようにします[20-22]。

### 3. 6/2で社長に決めてもらうべき事項
*   **サービス内容と対象ユーザー**：3つの方向性（A: AIフィット診断支援、B: Workspace連携型PM支援、C: AI PoC高速構築支援）から主軸を選び、最初に見せる相手（社内、既存顧客、見込み顧客）を決定します[23, 24]。
*   **優先開発機能と体制**：6/2以降の最初の2週間で作る最優先機能、3-tool体制でのAI月額コスト上限、寛太氏の関与度やチーム拡大（顧客3社同時パイロット時などの追加採用）の閾値を決定します[25-28]。
*   **AIエンジン選定方針**：サービス本体に組み込むAIをGeminiファミリー単一とするか、マルチAI並走にするかを決定します[29]。
*   **運用・公開・ツールの採用方針**：Google Workspace連携の運用範囲、公開URLの共有許容範囲と認証層追加（R10）、個人情報の法務確認時期（R9）、およびNotebookLM / Slack / Notion / Obsidianの正式導入優先順位を決定します[30-33]。

### 4. バックエンド/app.pyやデータ構造を肉付けする時に守るべき前提
*   **API制限時のフォールバック**：Gemini APIの制限時やCodex作業中は、必ず `AI_FORCE_MOCK=1` を設定してFastAPIを起動し、APIの追加消費を防ぎます[34]。
*   **AI復帰時のパイプライン**：バックエンドの deterministic fallback による事前解析・事前スコア結果は、live AI復帰時に `structured context` としてGeminiのプロンプトへ渡し、精度向上に利用します[35]。
*   **監査ログの管理**：`/api/parse` と `/api/match` の判定結果は原文を保存せず、要約・スコア・抽出スキルのみをローカルの `data/audit/ai_audit.jsonl` に保存します。このファイル自体はGit管理外とします[36, 37]。
*   **認証の固定化**：Workspace連携処理は `authorized_user.json` を使用し、Drive APIで実行アカウントが `k-umezawa@ml-mightylink.com` であることを事前検証してから実行します[38, 39]。
*   **データ構造と排他制御**：IndexedDBとSQLite3両対応のハイブリッド構成を想定します[40, 41]。競合を防ぐため `data/WBS.tsv` の直接編集権限はCodexのみが持ちます[42]。
*   **Seedance API連携の扱い**: ModelArk Seedanceの `content[{type,text}]` 形式のペイロードをデフォルトとし、別エンドポイント用には `SEEDANCE_PAYLOAD_STYLE=prompt_legacy` で退避できるようにします[43, 44]。また、非同期タスク結果の取得ポーリング（`SEEDANCE_RESULT_API_URL_TEMPLATE` への接続）に対応し[45, 46]、APIエラーは秘密情報を露出させないよう `fallback_reason` を通じて通知します[44]。外部API課金ガードダッシュボード（`/admin`）とローカル帳簿（`data/external_api_usage.jsonl`）で利用状況を管理します[47, 48]。

### 5. NotebookLM / Slack / Notion / Obsidian / GitHub Issues / GitHub Project の運用上の残課題
*   **NotebookLM**：CLI認証は補助ログイン導線で維持します[49]。要約（Agent Brief）取得に加え、社長説明用PowerPoint（PPTX）の生成とGoogle Drive共有まで完了しています[50, 51]。
*   **GitHub Project**：CLIの `read:project` スコープ不足によりブラウザ認証の復旧待ちです。未解決なら6/2デモからはProjectボードを除外します[52, 53]。
*   **Slack**：ローカルCLIおよび送信MCPツールが未露出のため、現状は投稿草稿の生成に留めています。6/2に投稿先と共有範囲の確認を行い、その後実送信連携を整えます[53]。
*   **Notion / Obsidian**：証跡ページやvault雛形は生成済みですが、公式管理台帳としての自動投稿や外部API連携の本実装は社長の判断待ちです[20, 54]。
*   **GitHub IssuesとTracker連携**：Issuesは実装タスク用、WBSは日程・報告用として相互参照します[55]。Sheetsの `課題管理表` と `QA表` はTSVからWBSと同一OAuthで一括同期する運用になっています[56-58]。

### 6. WBSへ追加すべき次アクション
*   **三ツール開発フローとCalendar運用 (T664/T666以降)**：毎セッションで公式Docs最新版を確認します[12]。また、Calendar同期時は「完了済みWBSイベント」を自動削除し、未完了や会議イベントだけを残すアクションビューとして運用を継続します[59, 60]。
*   **stale-docの能動的削除 (HANDOFF-12など)**：内容が古くなったドキュメント（未確認の未来モデル名など）は追記で温存せず、物理削除または現在形へ置換する「stale-doc削除ルール」を徹底します[60, 61]。
*   **6/2資料最終パックレビュー (T663)**：ハードゲート条件をクリアし、6/1に最終リハーサル（dry-run）を実施します[16]。
*   **決定事項の即時反映 (T701〜T708)**：6/2打ち合わせで決定したサービス方針に基づき、直ちに `data/WBS.tsv` へ対応フェーズ（A, B, Cのいずれか）のWBSテンプレを追加し、選ばれなかったフェーズの記述は削除した上でSheets/Calendar/Gitへ即時反映します[62-64]。

---
💡 **ご提案**:
こちらの要約内容をもとに、NotebookLMの「開発要約レポート（Tailored Report）」を作成することも可能ですが、作成いたしましょうか？

## Notebook Summary

NotebookLM summary command return code: `0`
