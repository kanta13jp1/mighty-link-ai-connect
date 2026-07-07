# Gemini モデル移行評価ログ (T780)

- 評価ID: `GEMINI_MODEL_MIGRATION_T780`
- 実施日: 2026-07-07
- 本番既定モデル: `gemini-3.5-flash`
- 公式Docs: https://ai.google.dev/gemini-api/docs/models (最終更新 2026-06-30 UTC)
- 判定: **ok** (10/10 仮説PASS)

## 10仮説検証

| # | 仮説 | 結果 | 根拠 |
| --- | --- | --- | --- |
| H1 | 本番既定モデルは公式docs(2026-06-30更新)のstable/GA最上位 gemini-3.5-flash である | PASS | production_default=gemini-3.5-flash / stable先頭=gemini-3.5-flash |
| H2 | シャットダウン済みモデル(2.0 Flash/Flash-Lite等)はblocked_model_patternsで拒否される | PASS | shutdown拒否={'gemini-2.0-flash': True, 'gemini-2.0-flash-lite': True, 'gemini-3-pro-preview': True, 'gemini-3.1-flash-lite-preview': True} |
| H3 | 本番コード(app.py, sales_email_parser.py)の既定モデルがpolicy production_defaultと一致 | PASS | app.py=gemini-3.5-flash / parser=gemini-3.5-flash / policy=gemini-3.5-flash |
| H4 | GEMINI_MODEL環境変数で本番既定を上書きでき、値がパイプラインに反映される | PASS | env上書き解決=gemini-2.5-flash / parser.model_name=gemini-2.5-flash |
| H5 | latest aliasは本番コードで未使用かつpolicyでブロックされる(hot-swap回避) | PASS | alias拒否=True / runtime使用=なし |
| H6 | API未設定時のdeterministic fallbackがEmailParseResultJSONスキーマ準拠出力を返す(モデル非依存の可用性) | PASS | project→project(OK); talent→talent(OK); other→other(OK) |
| H7 | 構造化出力契約(response_schema=EmailParseResultJSON)はモデル非依存で候補モデル間互換 | PASS | response_schema固定フィールド=['category', 'confidence', 'evidence_excerpt', 'project', 'talent'] |
| H8 | 同一入力へのfallback出力は決定的で、移行前後の回帰比較が可能 | PASS | 再実行一致=True |
| H9 | 本番切り替え手順(rollout/rollback、既定値は同一コミットで変更)がRunbookに明記されている | PASS | 手順書マーカー={'本番切り替え手順': True, 'ロールバック': True, '同一コミット': True} |
| H10 | policyのstable候補モデルは全てシャットダウン対象外で、監査上クリーン | PASS | stable候補=['gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro'] / ブロック該当=なし |

## ライブ比較 (任意・GEMINI_API_KEY必要)

- 未実施: --live未指定

## 結論

- 公式Docsでシャットダウン済みの Gemini 2.0 系はpolicyで拒否され、本番既定はstable最上位の `gemini-3.5-flash` を維持することが安全と確認した。
- 構造化出力契約はモデル非依存で、候補stableモデル間で互換。fallbackによりAPIモデルの可否に関わらず可用性が保たれる。
- ライブでの精度/latency/cost比較は `GEMINI_API_KEY` を設定して `--live` で実行する（本番相当の実値取得は運用者/Codexレーンが実施）。
