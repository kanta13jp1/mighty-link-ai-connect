# Codex 継続作業メモ

最終更新: 2026-07-19 / 管理レーン: Codex（現行化は Claude Code / T905）

本メモは **Antigravity + Gemini の quota を消費せずに開発を継続する** ための運用手順書です。
3レーン体制（Antigravity + Gemini / Codex / Claude Code）の役割分担は
[MULTI_AI_WORKFLOW.md](MULTI_AI_WORKFLOW.md) と `AGENTS.md` が正本です。

> [!NOTE]
> **作業履歴はここに書かない。** 過去の日次作業ログ（2026-05-21〜22 分・約925行）は
> 2026-07-19（T905）に削除しました。タスクの実施履歴は次が正本です:
> - **完了タスクと実施内容**: `data/WBS.tsv`（およびそこから生成される [WBS.md](WBS.md)）
> - **変更の詳細**: Git 履歴（`git log --follow <path>`。削除した作業ログも履歴から参照可能）
> - **運用手順**: [運用Runbookカタログ](OPERATIONS_RUNBOOK_CATALOG.md) 配下の各Runbook
> - **課題・QA**: `data/issues_tracker.tsv` / `data/qa_tracker.tsv`
>
> 本ファイルへ日付付きの作業ログを追記すると `tests/test_codex_continuation_notes_currency.py`
> が失敗します（append-only 肥大化の再発防止・150行上限）。

## 運用方針

- Antigravity + Gemini の quota が残っている通常時は、Antigravity を主作業環境として使う。
- Antigravity 側で Gemini quota 制限に達したら、Codex に切り替えて開発を継続する。
- コード実装・ドキュメント整備・ローカル検証・Git 操作は Codex で継続できる。
- FastAPI アプリは Gemini API が使えない場合でも mock fallback（決定論的フォールバック）で動作する。
- Google Sheets / Calendar / Drive 連携は `authorized_user.json` を使い、Workspace アカウント
  `k-umezawa@ml-mightylink.com` で実行する（`python scripts/verify_google_workspace_account.py` で検証）。
- Gemini API の quota を消費したくない場合は `AI_FORCE_MOCK=1` を付けてサーバーを起動する。

## Codex への切り替え手順

1. VSCode で本プロジェクト `mighty-link-ai-connect` を開く。
2. Codex に作業を引き継ぎ、実装・検証・ドキュメント更新を進める。
3. quota を温存する間は `AI_FORCE_MOCK=1` で FastAPI を起動し、AI fallback と Sheets 連携を確認する。
4. コミット前に `python scripts/run_lane_preflight.py`（全整合ガード）を実行する。
   セッション終了時は `--full`（ガード＋全テスト）で検証してから commit / push / main 反映まで行う。

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

`ai_force_mock` が `true`、`gemini_live` が `false` であれば Gemini quota を消費していません。

## Gemini 復帰時

quota が回復して live Gemini を使う場合は、`AI_FORCE_MOCK` を未設定に戻し、`GEMINI_API_KEY` を
設定してから `python src/app.py` を起動する。使用するモデル版は
[GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md](GEMINI_MODEL_VERSION_MIGRATION_RUNBOOK.md) の
追従ポリシーに従う（`scripts/audit_gemini_model_policy.py` が版ポリシー適合を検証）。
