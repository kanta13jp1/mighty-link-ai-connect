# Gemini CLI / Code Assist 残存依存監査レポート（T803）

作成日: 2026-06-17  
対象タスク: T803  
担当レーン: VSCode + Codex / Antigravity + Gemini  
関連: [MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) / [ANTIGRAVITY_CLI_EVALUATION_REPORT.md](ANTIGRAVITY_CLI_EVALUATION_REPORT.md) / [WBS.md](WBS.md)

---

## 結論

2026-06-18 に予定されている Gemini CLI / Gemini Code Assist 個人向け提供停止、および Firebase extension for Gemini CLI の終了に備え、リポジトリ内の残存依存を最終確認した。

結果として、CI、scripts、src、Firebase/Supabase 設定、VSCode 推奨拡張、AGENTS.md などの実運用ファイルには、Gemini CLI / Gemini Code Assist / Firebase Gemini CLI 拡張への現役依存は見つからなかった。Google系の開発レーンは、T693で評価済みの Antigravity CLI / Antigravity IDE を継続利用する。

## 公式情報の確認

今回の判断は、2026-06-17時点で以下の公式情報を確認して行った。

- [Google Developers Blog: Transitioning Gemini CLI to Antigravity CLI](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)
- [Gemini Code Assist consumer accounts](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals)
- [Firebase extension for Gemini CLI](https://firebase.google.com/docs/ai-assistance/gcli-extension)
- [Firebase release notes](https://firebase.google.com/support/release-notes)
- [Gemini API model docs](https://ai.google.dev/gemini-api/docs/models)

確認内容:

- 2026-06-18 以降、Gemini Code Assist for individuals / Google AI Pro / Google AI Ultra の Gemini CLI と Gemini Code Assist IDE extension はリクエスト提供を停止する。
- Gemini Code Assist Standard / Enterprise は別枠であり、今回の個人向け停止とは扱いが異なる。
- Firebase extension for Gemini CLI も同日に停止対象となるため、Firebase系のエージェント支援は Gemini CLI extension 経由ではなく Antigravity 側へ寄せる。
- Gemini API のモデル利用は CLI 停止とは別系統のため、本プロジェクトの Gemini API 連携自体は継続可能。

## 監査方法

`scripts/verify_gemini_cli_migration.py` を追加し、以下を分離して監査した。

- 実運用依存: `.github/`、`scripts/`、`src/`、`firebase.json`、`.firebaserc`、`supabase/`、`.vscode/extensions.json`、`AGENTS.md` など。
- 履歴参照: `docs/`、`data/WBS.tsv`、`exports/mighty_development_plan.ics` など。

検出対象:

- `gemini extensions install https://github.com/firebase/agent-skills/`
- `firebase/agent-skills` または `gcli-extension` の実運用利用
- `gemini auth` / `gemini chat` / `gemini extensions` などの Gemini CLI コマンド実行
- `google.geminicodeassist` など Gemini Code Assist IDE extension 推奨設定
- 実運用設定内での Gemini CLI 現役依存記述

## 監査結果

実行コマンド:

```powershell
python scripts/verify_gemini_cli_migration.py --project-root . --output-dir exports --date 2026-06-17
python -m pytest tests/test_gemini_cli_migration.py -q
```

結果:

- 実運用ファイルの残存依存: 0件
- 履歴参照: 11件（完了済みT803イベント削除後の最終ICS反映済み）
- Antigravity CLI: PATH上で検出済み
- Gemini CLI: PATH上で未検出
- pytest: 4件 PASS

生成物:

- `exports/gemini_cli_migration_audit.json`
- `exports/gemini_cli_migration_audit.md`

履歴参照として残っている `docs/ANTIGRAVITY_CLI_EVALUATION_REPORT.md`、`docs/MULTI_AI_WORKFLOW.md`、`docs/CODEX_CONTINUATION_NOTES.md`、`data/WBS.tsv` などの記述は、T693/T803 の移行経緯を示す証跡であり、現役の実行依存ではない。

## 今後のガードレール

- 本プロジェクトでは、Google系のエージェント開発レーンを Antigravity CLI / Antigravity IDE に寄せる。
- `gemini extensions install https://github.com/firebase/agent-skills/` を setup 手順、CI、scripts、docs の現役手順として追加しない。
- `.vscode/extensions.json` に `google.geminicodeassist` を推奨拡張として追加しない。
- Gemini API の利用は継続してよいが、Gemini CLI 依存とは明確に分ける。
- docs内に Gemini CLI の記述を残す場合は、移行履歴・停止対応・監査証跡であることを明示する。
