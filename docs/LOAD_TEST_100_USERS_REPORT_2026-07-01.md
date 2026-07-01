# T770 100同時ユーザー負荷テスト結果とスケーリング方針

- 生成日時: 2026-07-01T22:25:12+09:00
- 対応WBS: T770
- 関連リリース判定: PUBLIC-10
- 判定: FAIL
- シナリオ: 100同時ユーザー x 3リクエスト
- 総処理時間: 5.952 秒
- 対象: `GET /api/health`, `POST /api/parse`, `POST /api/match`
- 注意: CEO共有URLへ負荷をかけないため、FastAPI ASGIアプリをローカルプロセス内で実行し、SQLite/監査ログは一時ディレクトリへ隔離した。Gemini live call は `AI_FORCE_MOCK=1` で無効化した。

## SLA照合

| 指標 | 目標 | 実測 | 判定 |
| --- | ---: | ---: | --- |
| P50 | <= 1500 ms | 2324.88 ms | FAIL |
| P95 | <= 3000 ms | 3576.44 ms | FAIL |
| P99 | <= 8000 ms | 3583.86 ms | PASS |
| エラー | 0 件 | 0 件 | PASS |

## エンドポイント別結果

| エンドポイント | 件数 | 成功 | エラー | P50 | P95 | P99 | Max | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `/api/health` | 100 | 100 | 0 | 45.09 ms | 50.65 ms | 51.16 ms | 51.27 ms | `{"200": 100}` |
| `/api/match` | 100 | 100 | 0 | 3561.68 ms | 3581.88 ms | 3584.77 ms | 3585.1 ms | `{"200": 100}` |
| `/api/parse` | 100 | 100 | 0 | 2324.88 ms | 2410.57 ms | 2413.79 ms | 2414.02 ms | `{"200": 100}` |

## スケーリング方針

### Firebase Functions / Hosting

- Functionsは `maxInstances` を明示し、急なバーストでSupabase接続を枯渇させない。
- `minInstances` はcold startがP95を悪化させる証跡が出た場合に限り、コスト上限とセットで設定する。
- レスポンス後の暗黙バックグラウンド処理に依存せず、長時間AI処理は明示キューまたは人間レビュー導線へ分離する。

### Supabase

- Firebase/サーバーレス接続ではSupabase/Supavisor connection poolerを標準接続先にする。
- 関数インスタンスごとのDB接続数は小さく保ち、無制限な直結接続を避ける。
- T782で、実Supabase環境のpool size、リード分散、クエリ待ち時間を追加検証する。

### AI・レート制限

- Gemini/Seedanceの外部APIは引き続き日次上限、token上限、deterministic fallbackで保護する。
- 本番負荷テスト時は実ユーザーに近い分散IP/セッションで実施し、単一IPのレート制限により誤判定しない。

## PUBLIC-10 判定

本レポートにより、同時100ユーザー想定の代表API導線の負荷テストと初期スケーリング方針は完了した。
ただしSLA目標を満たしていないため、PUBLIC-10は `BLOCKED` のまま維持し、T858で改善と本番相当再試験を実施する。

## 公式ドキュメント確認メモ

- Firebase Functions manage functions: https://firebase.google.com/docs/functions/manage-functions?gen=2nd
- Firebase Functions tips: https://firebase.google.com/docs/functions/tips
- Firebase Hosting: https://firebase.google.com/docs/hosting
- Supabase connection pooler: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler
- Supabase connection management: https://supabase.com/docs/guides/database/connection-management
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions: https://docs.github.com/actions
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- Anthropic Claude Code overview: https://code.claude.com/docs/en/overview
