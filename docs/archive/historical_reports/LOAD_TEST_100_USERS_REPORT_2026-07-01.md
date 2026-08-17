# T858 100同時ユーザー負荷SLA再試験結果

- 生成日時: 2026-07-01T23:28:28+09:00
- 対応WBS: T858
- ベースラインWBS: T770
- 関連リリース判定: PUBLIC-10
- 判定: PASS
- シナリオ: 100同時ユーザー x 3リクエスト
- 総処理時間: 2.082 秒
- 対象: `GET /api/health`, `POST /api/parse`, `POST /api/match`
- deterministic fallback待機: parse 0.0 秒 / match 0.0 秒
- 捕捉した内部ログ行数: 500 行
- 注意: CEO共有URLへ負荷をかけないため、FastAPI ASGIアプリをローカルプロセス内で実行し、SQLite/監査ログは一時ディレクトリへ隔離した。Gemini live call は `AI_FORCE_MOCK=1` で無効化した。

## SLA判定

| 指標 | 目標 | 実測 | 判定 |
| --- | ---: | ---: | --- |
| P50 | <= 1500 ms | 508.52 ms | PASS |
| P95 | <= 3000 ms | 943.81 ms | PASS |
| P99 | <= 8000 ms | 1155.32 ms | PASS |
| エラー | 0 件 | 0 件 | PASS |

## エンドポイント別結果

| エンドポイント | 件数 | 成功 | エラー | P50 | P95 | P99 | Max | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `/api/health` | 100 | 100 | 0 | 52.52 ms | 59.55 ms | 60.44 ms | 60.65 ms | `{"200": 100}` |
| `/api/match` | 100 | 100 | 0 | 863.05 ms | 1133.85 ms | 1554.45 ms | 1615.74 ms | `{"200": 100}` |
| `/api/parse` | 100 | 100 | 0 | 508.52 ms | 789.79 ms | 857.71 ms | 868.59 ms | `{"200": 100}` |

## スケーリング方針

### Firebase Functions / Hosting

- Functionsは `maxInstances` を明示し、急なバーストでSupabase接続を枯渇させない。
- `minInstances` はcold startがP95を悪化させる証跡が出た場合に限り、コスト上限とセットで設定する。
- レスポンス後の暗黙バックグラウンド処理には依存せず、時間のかかるAI処理は明示キューまたは人間レビュー導線へ分離する。

### Supabase

- Firebase/サーバーレス接続ではSupabase/Supavisor connection poolerを標準接続先にする。
- FunctionsインスタンスごとのDB接続数は小さく保ち、無制限の直接接続を避ける。
- T782では実Supabase環境のpool size、read replica、クエリ待ち時間を追加検証する。

### AI・レート制限

- Gemini/Seedanceの外部APIは日次上限、token上限、deterministic fallbackで保護する。
- 本番負荷テスト時は実ユーザーに近い分散IP/セッションで実施し、単一IPのレート制限により誤判定しない。

## PUBLIC-10 判定

本再試験により、100同時ユーザー想定の代表API導線はエラー0で完走し、P50/P95/P99のSLA目標を満たした。
したがってPUBLIC-10は `PASS` とする。ただし、一般公開・有償ローンチは法務、課金、実メール接続、会社アカウント移管、Firebase CI/CDなど残ゲート完了後に再判定する。

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
