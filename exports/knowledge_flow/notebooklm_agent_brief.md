# NotebookLM Agent Brief

Generated: 2026-06-11T01:23:25+09:00
Notebook: `cd44c4ef-4c46-40b5-ace3-1b6904d29591`

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

Mighty Skill-Bridgeの開発ドキュメントに基づき、Codexおよび各AIエージェントが今後の開発を円滑に進めるための要約ブリーフを作成しました。

### 1. 現在のプロダクト方向性で確定していること
* **サービス方向性**: 6/2の社長打ち合わせを経て、**「方向性A：AIフィット診断支援」**（経歴書と案件票の4軸マッチング）として推進することが決定し、現在社内パイロット（人材担当・営業担当向け）を実施中です [1-3]。
* **開発体制**: 「Antigravity + Gemini」（フロント・マルチモーダル）、「VSCode + Codex」（バックエンド・CI・同期スクリプト）、「VSCode + Claude Code」（アーキテクト・設計・WBS調停）の**3-tool並走体制**で開発を進めています [4-6]。
* **インフラ・コスト**: Firebase（Hosting/Functions）とSupabase（PostgreSQL）を組み合わせたサーバーレス・BaaSハイブリッド構成を採用し、インフラ固定費を月額0円に抑える方針が確定しています [7, 8]。

### 2. 6/2の社長打ち合わせまでに優先すべきプレゼン準備タスク
*(※ フェーズ6の振り返り・完了済みタスク)*
* **公開デモの安定化・刷新**: Seedance API風のシネマティック動画デモUIへの刷新と、README fallbackを防ぐ「Public Demo Guard」の実装 [9-11]。
* **プレゼン資料の自動生成と美麗化**: NotebookLMで生成したスライド草案からPPTXを作成し、Canva/Figma MCP等を用いてブランドカラー（Mighty Blue等）を適用したリデザイン [12-15]。
* **Google Workspace管理基盤の同期**: `sync_wbs_to_sheets.py`等を用いたWBS、課題管理表、QA表のSheets自動同期（ガントチャート化）、および完了タスクのカレンダーイベント自動削除機能の実装 [16-18]。
* **開発ナレッジ連携の実体化**: Slack投稿草稿、Notion用CSV、NotebookLM投入資料などのデモ用ローカル成果物生成と証跡作成 [19, 20]。
* **フェイルオーバー導線の確保**: 公開URL障害時のローカルFastAPI起動や、Gemini API制限時でも動作するモックなどの代替導線準備 [21, 22]。

### 3. 6/2で社長に決めてもらうべき事項
*(※ プレゼンで提示された論点・判断材料)*
* **サービス方向性と対象ユーザー**: AI診断支援、PM支援、PoC構築支援の3択からどれを選ぶか、また社内/既存顧客/新規顧客のどこから着手するか [23, 24]。
* **最優先開発機能**: AIスコア根拠のUI化、案件ストック管理、WBS内製化など、2週間で優先すべき機能 [25]。
* **AIエンジンの運用・コスト**: Geminiファミリー単一かマルチAI並走か、また月額APIコストの上限（¥10,000 / ¥30,000 / ¥50,000 等）[26-28]。
* **公開範囲とセキュリティ**: 公開URLへの認証層追加の要否や、個人情報を取り扱う場合の法務確認時期 [27, 28]。
* **連携ツールの採用優先順位**: NotebookLM、Slack、Notion、Obsidianのうち、正式に運用フローへ組み込むツールの選別 [29]。

### 4. バックエンド/app.pyやデータ構造を肉付けする時に守るべき前提
* **APIのフォールバック仕様**: Gemini APIのQuota枯渇時でもサービスを止めないよう、`AI_FORCE_MOCK=1` による deterministic fallback（決定的ローカルモック）が動作する設計を維持してください [30-32]。
* **AI復帰時の橋渡し**: Gemini API復帰時は、ローカルの deterministic pre-parse / pre-score で得た構造化データを `structured context` としてGeminiのプロンプトに渡し、深い評価文やロードマップへ昇華させるパイプラインを守ってください [33]。
* **RLSと特権アクセスの分離（Supabase）**: フロントエンドからの直接アクセス（`anon`キー）には厳格なRow Level Security (RLS) を適用します。一方、ユーザー退会処理（物理削除）や監査ログ書き込みなどデータの直接更新・削除は、バックエンドの Cloud Functions 経由で `service_role` キーを使って特権実行する二重防御構造としてください [34-37]。
* **個人情報と監査ログの保護**: 個人識別情報（PII）はデータベース格納時に暗号化・マスキング（AES-256-GCM等）し、監査ログには原文全文ではなく要約やスコアのみを保存してください [38-40]。

### 5. NotebookLM / Slack / Notion / Obsidian / GitHub Issues / GitHub Project の運用上の残課題
* **NotebookLM**: 認証が切れやすいため、CLIでの同期時には補助ログインスクリプト（`notebooklm_login_workspace.py`）を経由する運用を継続する必要があります [41, 42]。
* **Slack**: ローカルCLIの未検出および送信MCPが未露出のため、現在は「投稿草稿の生成（`slack_ceo_update.md`）」に留まっています。投稿先チャンネルや共有範囲の社長承認後、Webhook等による実送信実装が必要です [43, 44]。
* **Notion & Obsidian**: 公式の意思決定ログや議事録（Notion/Docs）と、個人の開発思考メモ・ADR（Obsidian）の境界を明確にし、公式化されたものだけをGit・WBSへ昇格させる運用を徹底する必要があります [45]。
* **GitHub Project**: `gh auth refresh -s read:project -s project` のOAuthブラウザ認証が対話承認待ちでタイムアウト（401エラー）する課題が継続しており、IssueのProject Boardへの自動配置が滞っています [46, 47]。

### 6. WBSへ追加すべき次アクション
フェーズ8（本番運用・品質管理）およびフェーズ9（長期保守）に向けて、以下のタスクを優先してWBS上で推進・着手してください。
* **[T794] GitHub Project同期復旧**: Project item操作のための OAuth `read:project` 再承認と Issue の Board への自動配置復旧 [47]。
* **[T788] ステージング環境構築**: 本番反映前のプレビュー環境（Firebase Hosting preview / Supabase 検証用）の構築と JWTシークレット・DB分離ルールの整備 [48]。
* **[T789] 四半期セキュリティ監査**: `SECURITY_AUDIT_RUNBOOK.md` に基づく静的解析、依存ライブラリ監査、RLSポリシー検証の初回実施 [48]。
* **[T791] Stripe 課金実装**: Stripe Billing Meters API を用いた従量課金・Webhook検証・領収書メールのバックエンド実装 [49]。
* **[T790・T792] ユーザーサポート・法務対応**: 問い合わせ窓口（フォーム）の対応フロー整備や、特定商取引法に基づく表記・課金規約ページの整備 [48, 49]。
* **[T740・T741・T743] インフラ本番化**: カスタムドメインへのDNS移行、Supabaseの日次バックアップ自動化スクリプト実装、および Sentry / Google Cloud Monitoring 等を用いた死活監視とアラート設定 [50]。

## Notebook Summary

NotebookLM summary command return code: `0`
