# NotebookLM 同期タイムアウト対策 Runbook

作成日: 2026-06-21
対象WBS: T826 / T830

## 目的

`docs/` から Google Docs / Google Drive / NotebookLM sources へ同期する処理と、NotebookLM に長文回答を生成させる処理を分離する。

前回の同期では、Drive への取り込みと NotebookLM source 追加は完了した一方で、NotebookLM の `ask` 生成が長時間化し、セッション closeout 全体が不安定になった。今後は closeout の主判定を「source 同期完了」に置き、回答生成は必要時だけ別フェーズで実行する。

2026-06-21の再発（T830）では、`--skip-asks --skip-source-refresh --source-timeout-seconds 60` と `--drive-only` の両方が5分タイムアウトした。原因は NotebookLM CLI ではなく、`--drive-only` でも全 `docs/*.md` を毎回Google Docsへ再アップロードしていたことによるDrive同期時間の増大だった。

T830で `exports/knowledge_flow/notebooklm_docs_manifest.json` の `source_digest` とローカルmtimeを使う差分同期に変更した。未変更docsは既存Drive document IDを信頼してskipし、変更docsだけをDrive APIへ送る。全件再アップロードが必要な場合だけ `--force-drive-sync` を使う。

## 標準手順

### 1. Drive だけ同期する

NotebookLM CLI の状態に依存せず、Google Drive 側の docs 同期だけを更新する場合:

```powershell
python scripts/sync_docs_to_notebooklm.py --drive-only
```

通常は差分同期で動作する。T830検証では、94件中88件を未変更skip、6件だけアップロードし、32秒で完了した。

全docsを強制的にDriveへ再アップロードする場合:

```powershell
python scripts/sync_docs_to_notebooklm.py --drive-only --force-drive-sync
```

### 2. NotebookLM sources まで同期する

NotebookLM CLI にログイン済みで、NotebookLM notebook の source set を更新したいが、回答生成を待たない場合:

```powershell
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

T830検証では、Drive docs 94件をすべて未変更skipし、NotebookLM source refreshもskipして17秒で完了した。

このコマンドは次を行う。

- `docs/*.md` を Workspace 管理の Google Docs へ同期する。
- NotebookLM notebook に Drive docs を source として追加または更新する。
- manifest に Notebook ID が残っていない場合でも、同名の既存Notebookを再利用し、新規Notebookの重複作成を避ける。
- `--skip-source-refresh` 指定時は、既存sourceの強制refreshを同一closeout内では行わず、長時間化を避ける。
- `exports/knowledge_flow/notebooklm_agent_brief.md` と `notebooklm_ceo_slide_outline.md` には、source 同期完了を示すプレースホルダーを書く。
- `exports/knowledge_flow/notebooklm_docs_manifest.json` に `ask_generation.status = skipped` を記録する。

### 3. NotebookLM の回答生成を別実行する

Agent Brief や CEO Slide Outline を NotebookLM で再生成したい場合:

```powershell
python scripts/sync_docs_to_notebooklm.py --ask-timeout-seconds 900
```

既定の `NOTEBOOKLM_COMMAND_TIMEOUT_SECONDS` は 420 秒。長文回答生成だけを延長したい場合は、`--ask-timeout-seconds` で明示する。

## タイムアウト時の扱い

`notebooklm summary` または `notebooklm ask` がタイムアウトした場合、スクリプトは未処理例外で落とさず、該当コマンドの return code を `124` として manifest に記録する。

この場合でも、Drive 同期と NotebookLM source 同期が完了していれば、source set は次回の回答生成に再利用できる。

## 残留プロセス確認

NotebookLM CLI が長時間応答しない場合は、残留プロセスを確認する。

```powershell
Get-Process | Where-Object { $_.ProcessName -match 'python|notebook|chrome|msedge' } |
  Select-Object ProcessName,Id,CPU,WorkingSet |
  Sort-Object WorkingSet -Descending
```

不要なプロセスを終了する場合は、対象のプロセスIDを確認してから個別に終了する。無関係なブラウザやエディタをまとめて終了しない。

## 運用判断

- closeout を安定させたい: `--drive-only` または `--skip-asks`
- NotebookLM source の追加状態を保ちたい: `--skip-asks --skip-source-refresh --source-timeout-seconds 60`
- 既存sourceも強制refreshしたい: `--skip-asks --source-timeout-seconds 120` など、時間を取れる時に別実行する
- NotebookLM 生成物そのものが必要: `--ask-timeout-seconds 900`
- CLI 認証が切れている: `python scripts/notebooklm_login_workspace.py` を実行し、会社提供 Google アカウント `k-umezawa@ml-mightylink.com` でログインする
- Drive docsを強制再作成したい: `--force-drive-sync` を明示する。通常closeoutでは指定しない。

## 関連ファイル

- `scripts/sync_docs_to_notebooklm.py`
- `tests/test_sync_docs_to_notebooklm.py`
- `exports/knowledge_flow/notebooklm_docs_manifest.json`
- `exports/knowledge_flow/notebooklm_cli_next_steps.md`
- `exports/knowledge_flow/notebooklm_agent_brief.md`
- `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
