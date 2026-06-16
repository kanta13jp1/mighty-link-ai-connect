# Gemini CLI / Code Assist 残存依存監査レポート

- 監査日: 2026-06-17
- 生成時刻(UTC): 2026-06-16T17:08:23Z
- 総合判定: **OK**

## サマリー

- 実運用設定の残存依存: 0 件
- 実運用ファイルの走査数: 77 件
- docs/WBS 等の履歴参照: 11 件
- 履歴参照ファイルの走査数: 94 件

## 公式情報の確認結果

- [Google Developers Blog: Transitioning Gemini CLI to Antigravity CLI](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/): Gemini CLI / Gemini Code Assist individual requests stop on 2026-06-18; Antigravity CLI is the replacement lane.
- [Gemini Code Assist for individuals](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals): Consumer/individual Gemini Code Assist and Gemini CLI requests stop on 2026-06-18; standard and enterprise tiers are not impacted.
- [Firebase extension for Gemini CLI](https://firebase.google.com/docs/ai-assistance/gcli-extension): The Firebase extension for Gemini CLI stops working on 2026-06-18; migrate Firebase agent work to Antigravity CLI.
- [Firebase release notes](https://firebase.google.com/support/release-notes): Firebase repeats the 2026-06-18 Gemini CLI extension shutdown and directs users to Antigravity CLI / direct Firebase agent skills.
- [Gemini API model docs](https://ai.google.dev/gemini-api/docs/models): Gemini API model usage remains separate from deprecated Gemini CLI tooling.

## ツール確認

- antigravity_cli: available (C:\Users\kanta\AppData\Local\Programs\Antigravity IDE\bin\antigravity-ide.cmd) — Antigravity CLI is available on PATH.
- gemini_cli: not_found (-) — No local Gemini CLI executable was found on PATH.

## 実運用依存の検出結果

実運用ファイル（CI、scripts、src、Firebase/Supabase 設定、VSCode 推奨拡張、AGENTS.md 等）に、Gemini CLI / Gemini Code Assist / Firebase Gemini CLI 拡張への現役依存は見つかりませんでした。

## 履歴参照

docs/WBS/カレンダー成果物には移行経緯を説明する履歴参照が残っています。これらは実行依存ではなく、T693/T803 の証跡として保持します。

| 種別 | ファイル | 行 | 抜粋 |
| :--- | :--- | ---: | :--- |
| Gemini Code Assist IDE extension | `data/WBS.tsv` | 216 | T803	7. 決定後実行	インフラ	6/18 Gemini CLI / Code Assist 提供停止・Firebase 拡張終了に伴う残存依存の最終確認	Antigravity + 人間	Antigravity + Gemini	scripts/verify_gemini_cli_migration.py と pytestを追加し、2026-06-17に実運用77ファイルを監査。Gemini CLI / Gemini Code Assist / Firebase Gem |
| Gemini CLI named dependency | `data/WBS.tsv` | 216 | T803	7. 決定後実行	インフラ	6/18 Gemini CLI / Code Assist 提供停止・Firebase 拡張終了に伴う残存依存の最終確認	Antigravity + 人間	Antigravity + Gemini	scripts/verify_gemini_cli_migration.py と pytestを追加し、2026-06-17に実運用77ファイルを監査。Gemini CLI / Gemini Code Assist / Firebase Gem |
| Gemini CLI named dependency | `docs/ANTIGRAVITY_CLI_EVALUATION_REPORT.md` | 10 | Mighty Skill-Bridge プロジェクトでは、これまで Google公式AIツールとして `Gemini CLI` の採用を検討していましたが、Google Developer Blog にて **Gemini CLI から Antigravity CLI への移行** が正式アナウンスされました。 |
| Gemini CLI named dependency | `docs/ANTIGRAVITY_CLI_EVALUATION_REPORT.md` | 56 | - 旧 Gemini CLI に比べ、起動速度およびプロセス応答速度が劇的に向上しています。 |
| Gemini CLI named dependency | `docs/CODEX_CONTINUATION_NOTES.md` | 512 | - [x] 5/27 Antigravity 復帰後に Antigravity CLI 評価 (旧 Gemini CLI からの移行) — T693で完了 ([ANTIGRAVITY_CLI_EVALUATION_REPORT.md](ANTIGRAVITY_CLI_EVALUATION_REPORT.md))。なお 6/18 に Gemini CLI / Code Assist 個人向け提供停止のため、残存依存の最終確認を T803 で実施 |
| Gemini CLI named dependency | `docs/MULTI_AI_WORKFLOW.md` | 284 | - [x] Antigravity 復帰後 (5/27) に Antigravity CLI 評価 (旧 Gemini CLI からの移行) — [docs/ANTIGRAVITY_CLI_EVALUATION_REPORT.md](ANTIGRAVITY_CLI_EVALUATION_REPORT.md) にて完了 |
| Gemini Code Assist IDE extension | `docs/MULTI_AI_WORKFLOW.md` | 357 | - **Google（期限付き・最重要）**: **6/18 に Gemini CLI / Gemini Code Assist の個人向け提供が停止**し Antigravity CLI へ移行必須。Firebase の Gemini CLI 向け拡張も同日終了 — **T803 で残存依存監査を完了**し、実運用ファイルに Gemini CLI / Code Assist / Firebase Gemini CLI 拡張への現役依存がないことを確認済み（証跡: [GEMI |
| Gemini CLI named dependency | `docs/MULTI_AI_WORKFLOW.md` | 357 | - **Google（期限付き・最重要）**: **6/18 に Gemini CLI / Gemini Code Assist の個人向け提供が停止**し Antigravity CLI へ移行必須。Firebase の Gemini CLI 向け拡張も同日終了 — **T803 で残存依存監査を完了**し、実運用ファイルに Gemini CLI / Code Assist / Firebase Gemini CLI 拡張への現役依存がないことを確認済み（証跡: [GEMI |
| Gemini Code Assist IDE extension | `docs/WBS.md` | 258 | \| **T803** \| 7. 決定後実行 \| インフラ \| 6/18 Gemini CLI / Code Assist 提供停止・Firebase 拡張終了に伴う残存依存の最終確認 \| Antigravity + 人間 \| Antigravity + Gemini \| scripts/verify_gemini_cli_migration.py と pytestを追加し、2026-06-17に実運用77ファイルを監査。Gemini CLI / Gemini Code Ass |
| Gemini CLI named dependency | `docs/WBS.md` | 258 | \| **T803** \| 7. 決定後実行 \| インフラ \| 6/18 Gemini CLI / Code Assist 提供停止・Firebase 拡張終了に伴う残存依存の最終確認 \| Antigravity + 人間 \| Antigravity + Gemini \| scripts/verify_gemini_cli_migration.py と pytestを追加し、2026-06-17に実運用77ファイルを監査。Gemini CLI / Gemini Code Ass |
| Gemini CLI named dependency | `docs/WBS_PROCESS_COVERAGE_AUDIT_2026-06-13.md` | 43 | **固定アンカー（動かさない）**: T746 Go/No-Go（6/16 定例レビュー連動）、T803 Gemini CLI 停止対応（外部期限 6/18）、T798 法務確認（人間ゲート、6/16 まで）、T802 監査修正（SLA 6/19）、T808 月次配信（7/1 月次サイクル）、T741/T743/T745（既に最速）。 |

## ガードレール

- Do not add `gemini extensions install https://github.com/firebase/agent-skills/` to scripts, CI, or setup docs.
- Do not require `google.geminicodeassist` or the individual Gemini Code Assist IDE extension in .vscode recommendations.
- Use Antigravity CLI / Antigravity IDE for the Google agent lane; keep Gemini API usage as API/model integration only.
- Keep historical docs only when they explicitly describe the migration or shutdown context.
