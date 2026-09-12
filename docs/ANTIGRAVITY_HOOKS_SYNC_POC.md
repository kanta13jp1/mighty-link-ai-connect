# Mighty Skill-Bridge：Antigravity Lifecycle Hooks 設計およびセッション自動記録仕様レポート（T695）

**作成日**: 2026年6月3日（最終改訂: 2026年8月22日）
**ステータス**: 設計・実装改訂  
**対象フェーズ**: 7. 次期開発・運用（連携）  
**関連タスク**: **T695** Antigravity hooks機能による自動記録・同期スクリプト連携の設計・検証、**T992** Stop Hook実行パスの移植性修復と実コマンド回帰検証
**関連Issue/課題**: [R4](../data/issues_tracker.tsv#L5) (同期漏れ・セッションドリフトによる成果物不整合リスク)

---

## 1. 背景と目的
Mighty Skill-Bridge の開発は、Antigravity + Gemini、Codex、Claude Code の3つのAIツールが役割分担（レーン）を行いながら並行して進められています。
各AIレーンがどのような作業・指示・変更・アクションを行ったかを自動追跡し、セッションログとして `docs/sessions/` および Obsidian Vault に確実に記録することは、ナレッジの属人化とセッションドリフトを防止する上で極めて重要です。

本設計では、Google Antigravity 公式仕様（`.agents/hooks.json`）に準拠した **Lifecycle Hooks** を定義し、セッション終了時（`Stop` イベント）に自律的にセッション履歴とサニタイズされた証跡を記録する構成を策定・実装します。

---

## 2. 公式 Hooks 構成設計（.agents/hooks.json）
ワークスペースのルートに [.agents/hooks.json](../.agents/hooks.json) を配備し、公式の `Stop` ライフサイクルイベントハンドラーを定義しています。

```json
{
  "session-log-recorder": {
    "enabled": true,
    "Stop": [
      {
        "type": "command",
        "command": "python -c \"import sys, subprocess, pathlib; cwd = pathlib.Path.cwd(); candidates = [cwd / 'scripts' / 'record_session_log.py', cwd.parent / 'scripts' / 'record_session_log.py']; target = next((c for c in candidates if c.is_file()), None); sys.exit(1) if target is None else sys.exit(subprocess.run([sys.executable, str(target)]).returncode)\"",
        "timeout": 30
      }
    ]
  }
}
```

Antigravity IDE では Hook コマンドの作業ディレクトリが `.agents/` になる実行例があるため、プロジェクトルートと `.agents/` のどちらから起動されても `scripts/record_session_log.py` を相対探索できるようにしています。ユーザー固有の絶対パスは設定に保存しません。

### 2.1 入出力プロトコル契約
1. **標準入力 (stdin)**:
   - Antigravity 実行エンジンから JSON ペイロード（`conversationId`, `transcriptPath`, `workspacePaths`, `terminationReason`, `fullyIdle`）を受信。
2. **標準出力 (stdout)**:
   - 公式 `Stop` 仕様に従い、`{"decision": "allow"}` の純粋な JSON を出力。
   - 実行時の詳細・警告メッセージはすべて `sys.stderr` に出力して JSON 出力を汚染しない。
3. **セキュリティ & PII サニタイズ**:
   - メールアドレス、電話番号、OpenAI/Gemini/GitHub/AWS/Slack トークン、データベースパスワード、秘密鍵、`.env` などの機密文字列を正規表現で自動検知し、`[REDACTED_*]` に置換。

---

## 3. 実装および自動テスト検証

### 3.1 ユニットテストスイート (`tests/test_session_log_recorder.py`)
- `test_agents_hooks_json_specification_compliance`: `.agents/hooks.json` のスキーマ検証
- `test_configured_stop_hook_command_executes_from_agents_directory`: `.agents/` を作業ディレクトリとして設定済みコマンドそのものを実行し、絶対パス非依存、stdin/stdout契約、ログ生成を検証
- `test_hook_stdin_stdout_contract_with_decision_allow`: 標準入力 JSON 読込と `{"decision": "allow"}` 出力検証
- `test_accurate_file_modification_and_exclusion`: 閲覧ツール（`view_file`）および外部パス除外の検証
- `test_comprehensive_secret_and_pii_redaction`: PII・APIキー・接続文字列・秘密鍵の包括的マスキング検証
- `test_session_deduplication_and_in_place_update`: 同一 Conversation ID におけるインプレース更新・重複防止検証

---

## 4. 運用上の留意事項
- Antigravity IDE / CLI の実行ループ停止時に `.agents/hooks.json` が読み込まれ、自動的に [`docs/sessions/`](sessions/) および [`docs/SESSION_LOG.md`](SESSION_LOG.md) へ最新の作業概要が記録されます。
- 同一セッション内で複数回の実行停止が発生した場合は、Conversation ID に基づき同一ログファイルが最新状態で上書き更新（インプレース更新）されます。
