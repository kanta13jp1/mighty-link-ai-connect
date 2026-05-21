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
  "ai_mode": "mock_fallback",
  "ai_force_mock": true
}
```

## Gemini 復帰時

quota refresh 後に live Gemini を使う場合は、`AI_FORCE_MOCK` を未設定に戻し、`GEMINI_API_KEY` を設定してから `python src/app.py` を起動する。
