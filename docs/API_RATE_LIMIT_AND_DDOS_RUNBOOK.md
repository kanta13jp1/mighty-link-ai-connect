# API レート制限・DDoS 緩和 Runbook

**関連 WBS**: T753
**関連課題**: R61
**対象**: FastAPI (`src/app.py`) / Firebase Hosting / Cloud Run / Supabase / Google Workspace 連携

## 目的

Mighty Skill-Bridge の公開デモおよび将来の本番 API で、過剰リクエストによる Gemini / Seedance / Google Sheets 呼び出しの浪費、認証画面への総当たり、CPU/DB 負荷の急増を抑える。

本実装は FastAPI プロセス内のバックストップであり、DDoS の第一防衛線は Firebase Hosting / Cloud Run 前段、必要に応じた Cloud Armor、App Check、CDN/WAF、Supabase 側の接続上限・RLS で担う。

## 現在の適用範囲

| 種別 | 対象 | 既定値 |
| --- | --- | --- |
| ヘルスチェック除外 | `/`, `/api/health`, `/favicon.ico`, Chrome DevTools workspace route | 制限なし |
| 高コスト API | `POST /api/parse`, `POST /api/match`, `POST /api/seedance/video-demo`, `POST /api/sync` | 20 req / 60 sec / client |
| 成果物生成 | `POST /api/knowledge-flow/generate` | 6 req / 60 sec / client |
| 管理・認証系 | `/admin`, `/admin/usage`, `/api/admin/*`, `/api/audit/recent`, `/api/db-test`, `/exports/*` | 30 req / 60 sec / client |
| 一般 API | その他 `/api/*` | 120 req / 60 sec / client |

超過時は HTTP `429` を返し、`Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` ヘッダーを付与する。

## 環境変数

| 変数 | 既定値 | 用途 |
| --- | ---: | --- |
| `RATE_LIMIT_ENABLED` | `true` | レート制限の有効化。障害時の一時切り戻しのみ `0` |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | 集計ウィンドウ秒数 |
| `RATE_LIMIT_MAX_REQUESTS` | `120` | 一般 API 上限 |
| `RATE_LIMIT_AUTH_MAX_REQUESTS` | `30` | 管理・認証・exports 上限 |
| `RATE_LIMIT_EXPENSIVE_MAX_REQUESTS` | `20` | Gemini / Seedance / Sheets 系の高コスト API 上限 |
| `RATE_LIMIT_GENERATION_MAX_REQUESTS` | `6` | NotebookLM/Drive 向け成果物生成 API 上限 |

## 検証

```powershell
python -m pytest tests/test_api.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

手動確認:

```powershell
$body = @{ prompt = "rate limit test" } | ConvertTo-Json
1..25 | ForEach-Object {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/seedance/video-demo" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
  } catch {
    $_.Exception.Response.StatusCode.value__
  }
}
```

## 運用方針

1. 通常デモは既定値のまま運用する。
2. 有償プラン開始時は、Cloud Run の同時実行数・最大インスタンス数、Firebase App Check、Cloud Armor rate-based rule、Supabase connection pool の順に前段保護を追加する。
3. `429` が通常ユーザーで頻発する場合は、`/api/admin/usage` と Cloud Logging で高コスト API の呼び出し元・時刻・経路を確認してから上限値を調整する。
4. 攻撃疑いの場合は、`RATE_LIMIT_EXPENSIVE_MAX_REQUESTS` と `RATE_LIMIT_AUTH_MAX_REQUESTS` を一時的に下げ、必要なら Firebase/Cloud Run 側で該当 IP / ASN / 国別制御を実施する。
5. プロセス内 limiter はインスタンスごとに独立するため、複数インスタンスで厳密な全体制限が必要になった時点で Redis / Memorystore / Cloud Armor へ移行する。

## 公式ドキュメント確認メモ

- Google Cloud Armor rate limiting: <https://cloud.google.com/armor/docs/rate-limiting-overview>
- Firebase App Check: <https://firebase.google.com/docs/app-check>
- Supabase RLS / database security: <https://supabase.com/docs/guides/database/postgres/row-level-security>
- FastAPI / Starlette middleware: <https://www.starlette.io/middleware/>

## 変更履歴

| 日付 | 変更 |
| --- | --- |
| 2026-06-14 | T753 で FastAPI 共通レート制限 middleware、`src/rate_limit.py`、pytest、R61 を追加 |
