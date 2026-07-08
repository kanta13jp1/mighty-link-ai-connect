# リード負荷分散シミュレーション (T782)

- レポートID: `READ_LOAD_DISTRIBUTION_T782` / 実施日: 2026-07-08
- 判定: **ok** (10/10 仮説PASS)
- トラフィック基準: load_test_100_users_2026-07-01.json burst 144.1 req/s
- 前提: DB占有 25.0ms/req、POOL_MAX 4/インスタンス、Supavisor予算 200 client conns

## 10仮説検証

| # | 仮説 | 結果 | 根拠 |
| --- | --- | --- | --- |
| H1 | 現行プールはThreadedConnectionPool(min1/max4/recycle1800s/Supavisor mode検出)である | PASS | app.py実装確認: pool種別/既定値/mode検出すべて存在 |
| H2 | APIはread(GET)がwriteより多く、read offloadの余地がある | PASS | read 21 / write 14 (read share=60%) |
| H3 | read-after-write整合が必要なGETを特定し、それ以外をレプリカ安全群に分類できる | PASS | primary固定=['/api/auth/me', '/api/engineers', '/api/jobs', '/api/matches'] / レプリカ安全=17件 (read内81%) |
| H4 | Erlang C実装は既知の理論値と一致する | PASS | M/M/1(ρ=0.6)→0.600(=0.6期待) M/M/2(a=1)→0.3333(=0.3333期待) |
| H5 | 現行実測バースト負荷では1インスタンスのプール(c=4)が飽和せず、P95待ちがプール待ち予算(SLA比10%)内 | PASS | 実測バースト144.1req/s・DB占有25.0ms・c=4: 利用率90% P95待ち173.51ms(予算300ms=SLA比10%以内。ただし利用率90%で余裕薄→水平スケール前提を設計に明記) |
| H6 | アクセス10倍ではprimary-only・c=4は飽和し、スケール施策が必須になる | PASS | 10倍負荷(1441.0req/s)でc=4は飽和(要スケール) |
| H7 | レプリカoffloadは高負荷時のprimary必要インスタンス数を削減する | PASS | 10倍負荷(1441.0req/s)の必要インスタンス数(利用率≤80%): primary-only 12台 → レプリカoffload後 6台 (offload率49%で必要台数を削減) |
| H8 | インスタンス数×プールサイズの安全式がSupavisorクライアント接続予算内に収まる | PASS | 推奨maxInstances(20) × POOL_MAX(4) = 80 ≤ Supavisor予算200 |
| H9 | 現行コードはtransaction pooler(6543)の制約(session state不可)に抵触しない | PASS | session state SQL(SET/LISTEN/PREPARE/DECLARE)使用=なし(transaction mode安全) |
| H10 | T866同期init後の実負荷テスト(100ユーザー)がSLA greenで回帰しない | PASS | load_test_100_users_2026-07-08.json: errors=0 p95=1113.31ms (SLA 3000ms) sla_keys=['targets_ms', 'overall_pass', 'endpoint_results'] |

## 負荷シナリオ (Erlang C, c=4/インスタンス)

| 負荷 | req/s | primary単独 利用率 | P95待ちms | レプリカoffload後 利用率 | P95待ちms |
| --- | --- | --- | --- | --- | --- |
| 1x | 144.1 | 90% | 173.51 | 46% | 11.97 |
| 2x | 288.2 | 飽和 | None | 93% | 239.63 |
| 5x | 720.5 | 飽和 | None | 飽和 | None |
| 10x | 1441.0 | 飽和 | None | 飽和 | None |

## プールサイズ掃引 (10倍負荷)

| c | 利用率 | 待ち確率 | P95待ちms |
| --- | --- | --- | --- |
| 2 | 飽和 | 1.0 | None |
| 4 | 飽和 | 1.0 | None |
| 6 | 飽和 | 1.0 | None |
| 8 | 飽和 | 1.0 | None |
| 10 | 飽和 | 1.0 | None |
| 12 | 飽和 | 1.0 | None |
| 14 | 飽和 | 1.0 | None |
| 16 | 飽和 | 1.0 | None |
| 18 | 飽和 | 1.0 | None |
| 20 | 飽和 | 1.0 | None |

詳細な設計判断は docs/DB_READ_LOAD_BALANCING_DESIGN.md を参照。
