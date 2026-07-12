# Multi-AI 開発ワークフロー

更新日: 2026-06-23
担当レーン: VSCode + Codex  
関連: [WBS.md](WBS.md) / [WBS_SYNC_GUIDE.md](WBS_SYNC_GUIDE.md) / [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) / [CODEX_CONTINUATION_NOTES.md](CODEX_CONTINUATION_NOTES.md)

---

## 目的

Mighty-Link AI Connect は、Antigravity + Gemini、VSCode + Codex、VSCode + Claude Code の三つを役割分担して使う。各セッションで同じ品質ゲートを通し、WBS、課題管理表、QA表、Google Sheets、Google Calendar、GitHub Issues、GitHub Project の状態がずれないようにする。

この文書は毎回の開発開始から closeout までの標準手順を定義する。古いモデル名、未確認の未来機能、解決済みの暫定ブロッカー、古い同期件数は現行ガイドとして残さない。

---

## レーン分担

| レーン | 主担当 | 使う場面 |
| --- | --- | --- |
| Antigravity + Gemini | UI、マルチモーダル、ブラウザ確認 | フロントエンド polish、画像・動画・音声を含むデモ、視覚確認、Gemini API の現行モデルを使う検証 |
| VSCode + Codex | 実装、同期、自動化、GitHub | FastAPI、Firebase/Supabase、Google Workspace API、CI、GitHub CLI、WBS/Sheets/Calendar同期、public demo guard |
| VSCode + Claude Code | ドキュメント、レビュー、triage | 仕様・議事録・Runbook、WBS網羅性監査、PRレビュー、課題/QAの整理、古いdocsの削除判断 |

競合しそうなときは、WBSの該当タスクと `data/WBS.tsv` を正本にする。ドキュメントだけで状況を確定せず、最後に同期スクリプトと GitHub の状態で確認する。

---

## セッション開始ゲート

1. `docs/` の関連文書を読む。今回の作業に直接関係する要件、設計、Runbook、WBSを優先する。
2. 公式ドキュメントの最新版を確認する。広い一覧を毎回確認しつつ、今回の作業に影響するものは必ず根拠として使う。
3. 今日完了するWBSタスクを一つ決める。不足タスクが見つかった場合は `data/WBS.tsv` に追加し、同じセッションで完了できる範囲なら完了まで進める。
4. 課題やQAが発生したら、`data/issues_tracker.tsv` と `data/qa_tracker.tsv` に反映する。
5. secret、OAuth token、実メール本文、個人連絡先、FTP/DB/Stripeの認証情報は GitHub、Sheets、Issue、Slack、Notion、NotebookLM、docs に記録しない。

---

## 公式Docs確認対象

毎セッションで以下を確認する。作業対象に該当しないものは「影響なし」として扱い、docsに長い引用や古いモデル名を残さない。

| 領域 | 公式確認先 |
| --- | --- |
| Anthropic / Claude Code | Claude Code overview、memory、settings、security |
| OpenAI / Codex | Codex overview、AGENTS.md、best practices、MCP、Codex manual |
| Google / Gemini / Workspace | Gemini models、context caching、Sheets batchUpdate、Firebase docs |
| Microsoft | Microsoft Foundry、Azure OpenAI / Foundry Models |
| Meta / Llama | Llama docs、Meta公開ページ、公式Llama GitHub |
| Amazon | Amazon Bedrock user guide |
| Apple | Machine Learning、Human Interface Guidelines |
| xAI / Grok | xAI docs |
| Kimi / Moonshot | Kimi API docs |
| MiMo | XiaomiMiMo/MiMo 公式GitHub |
| DeepSeek | DeepSeek API docs |
| ByteDance / BytePlus | Seedance、BytePlus ModelArk docs |
| GitHub | Issues、Projects、Actions、Pages、secrets |
| Slack | Slack Developer Docs |
| Notion | Notion API docs |
| Obsidian | Obsidian Help |
| Unity | Unity docs / Unity Manual |
| Figma | Figma REST / Plugin docs |
| Canva | Canva Apps SDK docs |
| Reddit | Reddit Devvit docs |
| InsForge | InsForge docs、`https://insforge.dev/skill.md` |
| Firecrawl | Firecrawl docs |
| Discord | Discord Developer docs |
| Stripe | Billing、Customer Portal、Tax、API reference |
| Supabase | Supabase docs、changelog、RLS、Postgres upgrade notes |
| お名前.com | お名前.comヘルプ、ドメイン/DNS/WordPress/FTP関連 |

2026-07-04 時点の確認メモ:

- Codex manual は `fetch-codex-manual.mjs` で最新版を取得してから、AGENTS.md、MCP、skills、GitHub連携の判断に使う。
- GitHub Projects は Project #1 `Mighty Skill-Bridge` を正とし、Issueを追加したらStatusをDoneまで更新する。
- Gemini API の現行安定版は 3.5 Flash / 3.1 Flash-Lite。Gemini 2.0 系はシャットダウン済み。本番既定は `gemini-3.5-flash`（QA-89）で、T780 の移行評価はGA後（2026-07-09〜）に実施する。
- Stripe は当面実課金なし。2026-07-03のT861スコープ再定義（当面社内利用のみ）により、T791は課金の仕組み実装まで、T807 live有効化・T813 Stripe Tax・T793一般告知はT862有償化判断後へ移管した。料金はT860仮決定を承認済み（docs/PRICING_PLAN_PROVISIONAL_2026-07-03.md）。Stripe公式はレガシーtest modeでなくSandboxes（live設定から完全分離・最大5個）を推奨するため、T791は専用Sandboxで実装する（2026-07-04確認）。
- public_paid_launchゲートの社内GA向け仕分けはT863でドラフト済み（docs/GO_NO_GO_GATE_TRIAGE_2026-07-04.md）。T833（7/7）で承認後にdata/release_go_no_go_criteria.tsvへ反映する。
- CEO定例は2026-07-08(水)15:00に確定（6/29チャット、T819）。事前レポート・アジェンダはdocs/CEO_MEETING_AGENDA_2026-07-08.md（T864）。営業メール接続情報の受領待ち（R113）が最優先協議事項で、GA扱いは案A/案Bを定例で判断する。
- 本番Supabaseは**PostgreSQL 17.6**（2026-07-04 T811で確認、T837不要判定・完了）。PG14 EOLの影響なし。将来のメジャーアップグレードはSUPABASE_POSTGRES_UPGRADE_RUNBOOK.mdを使う。
- Supabase Daily Backup CIは6/22以降未稼働（R116）。WIFが旧プロジェクト（d7fa2）へ誤バインドされておりT852と同根。恒久修復はT870、暫定ローカルバックアップは7/4取得済み。本番スキーマの残存migration適用はT871（R117）。
- InsForge は導入判断前に `skill.md` を確認する。現行バックエンド方針は Firebase、DBは Supabase のままにする。
- OWASP WSTG / ZAP 相当の外部疑似診断はT805で実施済み。High 0 / secret-like値露出 0 を維持し、T835でFirebase Hosting本番URLのCSP等ヘッダhardeningを完了済み。GitHub Pagesは任意HTTPヘッダを設定できないためcontrolled demo mirrorとして扱う。
- WBSスケジュールは 2026-07-03 に再ベースライン済み（T859、[WBS_REVIEW_2026-07-03.md](WBS_REVIEW_2026-07-03.md)）。2026-07-08は社内向けGA（internal launch）、Phase 7-9最終完了2026-07-15をアンカーとし、人間依存ゲートの必着日はR111で追跡する。有償公開・live課金は時期未定でT862の月次レビューが管理する（[INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md](INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md)）。

2026-07-12 時点の確認メモ（T889）:

- Claude Code 公式 overview を再確認。CLAUDE.md / auto memory・skills・hooks・test-first ワークフロー（テストを書く→実行→修正）が推奨で、本プロジェクトのテストファースト方針と整合。2026年の新機能は routines / background agents / web・desktop サーフェス。
- Firebase Hosting 公式を再確認。CLI デプロイ＋Emulator Suite でのローカル検証、preview channels による staging 分離、GitHub 連携、rollback 付き一発デプロイが推奨。既存の [STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md](STAGING_ENVIRONMENT_OPERATION_RUNBOOK.md) と整合。
- Supabase docs トップは一般案内のみで具体的な方針変更なし。本番 PostgreSQL 17.6 継続・RLS 有効の方針は不変。
- 工程網羅の判定を手動監査（06-13 / 06-25）から**自動10仮説ガード** [WBS_LIFECYCLE_COVERAGE_GUARD.md](WBS_LIFECYCLE_COVERAGE_GUARD.md) へ移行（T889）。企画→保守の7工程・お名前.com/Firebase/Supabaseの網羅と日程非逆転（開始日≤終了予定日）を CI で継続検証する。T811/T837 の日程逆転を検出・修正済み。
- GitHub Issues/Projects 公式を再確認。Issue メタデータ（labels/milestones/sub-issues/dependencies）は Project #1 に統合され、ビュー/フィルタで進捗管理できる。Google Sheets API batchUpdate 公式を再確認し、バッチ一括更新・field mask による部分更新・RepeatCellRequest 等が推奨。どちらもトラッカー→Sheets/GitHub 同期の方針と整合。
- トラッカー TSV（課題管理表/QA表/テスト結果/リリース判定）の構造・参照整合を**自動10仮説ガード** [TRACKER_INTEGRITY_GUARD.md](TRACKER_INTEGRITY_GUARD.md) で CI 検証（T890）。ラグド行・重複ID・不正状態・不正日付・WBS/QA/R 参照切れが Sheets 同期前に落ちる。現状ドリフト0。

---

## WBSと同期

`data/WBS.tsv` が正本。`docs/WBS.md` は `python scripts/generate_wbs_md.py` で再生成する。

完了したタスクは次を行う。

1. `data/WBS.tsv` の状態を `完了` にする。
2. `docs/WBS.md` を再生成する。
3. 必要な課題/QAを tracker TSV に反映する。
4. `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` を実行する。
5. `python scripts/sync_wbs_to_calendar.py` を実行する。完了済みWBSに紐づくCalendarイベントは削除される。
6. GitHub Issue と Project #1 を更新する。

---

## closeout

プロジェクト挙動またはdocsを変えたセッションでは、次を実行する。

```powershell
python scripts/generate_knowledge_flow_demo.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

NotebookLM向けdocsを変更した場合は、追加で次を実行する。

```powershell
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
python scripts/generate_ceo_presentation_deck.py
python scripts/upload_notebooklm_docs_to_drive.py
```

最後に commit、push `main`、`main` から `master` へ反映し、GitHub Pages のCEO共有URLを守る。

---

## 今回の反映

- 2026-07-08（T778_1）: SLA計測ビューのオフライン検証（列ドリフトガード＋閾値ロジック10仮説）を完遂。公式Docs refreshの要点: **Stripe usage-based billingは新規実装がMetronome推奨へ転換し、Billing Metersはlegacy/メンテナンスモード扱い**（T791実装時＝T862有償化判断後は、Billing Meters前提を見直しMetronome移行ガイドを確認する。QA-97/QA-101関連）。Gemini 2.0 Flashは正式に「Shut down」で移行必須（T780の判定を再確認、本番はgemini-3.5-flash維持）。Supabase RLSはポリシーを`(select auth.uid())`でラップし対象列にインデックス推奨、PG15+ビューは`security_invoker=true`でRLS継承。Firebase HostingはSSRを次世代App Hostingへ誘導（静的/SPAは従来Hosting継続）。
- 2026-07-07（T833/T875）: 10仮説検証で社内GA Go/No-Go判定（条件付きGo・案A）を実施し、判定チェックリストのDNS診断スクリプト文字コード不具合（R118）を修正した。公式Docs refreshの要点: Claude Fable 5 GA（`claude-fable-5`・2026-06-09）/ Claude Opus 4.1 は 2026-08-05 リタイア予定 / Sonnet 5 導入価格は 2026-08-31 まで / 旧 `docs.anthropic.com` は `platform.claude.com` へ移転。Gemini 安定版最上位は 3.5 Flash（2.0 Flash 系はシャットダウン対象 → T780 で確認）。Stripe API は 2026-06-24.dahlia でレガシー従量課金 Billing・`redirectToCheckout()` を削除（T791 実装時は新 Billing/Checkout API 前提・QA-97）。Firebase Studio は deprecated。Claude Code は Routines / Channels / `--teleport` / WinGet 配布が追加。
- T827として、毎セッションの公式Docs確認対象と3ツール運用ゲートを再整備した。
- T805として、非破壊の外部ペネトレーション疑似診断を実施し、High 0 / secret-like値露出 0 を確認した。
- T835として、Firebase Hosting本番URLにCSP / X-Content-Type-Options / Referrer-Policy / Permissions-Policy / frame protection / HSTSを設定し、R94/SEC-008を解決した。
