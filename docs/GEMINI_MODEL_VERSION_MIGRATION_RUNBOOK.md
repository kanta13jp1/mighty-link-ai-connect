# Gemini APIモデル追従・移行Runbook

- 作成日: 2026-07-01
- 対象WBS: T769
- 後続WBS: T780
- 正本データ: `data/gemini_model_policy.json`
- 監査スクリプト: `scripts/audit_gemini_model_policy.py`
- 監査証跡: `exports/gemini_model_policy_audit.json`, `exports/gemini_model_policy_audit.md`

---

## 目的

Gemini APIのモデル名、安定版/preview/廃止状況、`latest` aliasの扱いを毎回の開発セッションで確認し、アプリ本番の既定モデルを黙って差し替えないための標準手順を定める。

このRunbookの完了により、T769は「モデル追従プロセスが標準化され、古い/危険なモデル指定が検出可能になった」状態として扱う。実際の品質評価、本番切り替え、費用/latency比較はT780で実施する。

## 2026-07-01時点の採用方針

| 項目 | 方針 |
| --- | --- |
| 本番既定モデル | `gemini-3.5-flash` |
| 本番で許可するモデル種別 | 公式Docs上のspecific stable model stringのみ |
| `latest` alias | 本番既定値・本番コードでは禁止。hot-swapによる挙動変化を避ける |
| previewモデル | T780などの評価タスクでのみ使用可。public_paid_launchの既定値にはしない |
| 廃止/停止モデル | `data/gemini_model_policy.json` の `blocked_model_patterns` で検出し、監査を失敗させる |
| fallback | `GEMINI_API_KEY` 未設定またはAPI失敗時はdeterministic fallbackを維持する |

Google公式モデル一覧では、Geminiモデルはstable/preview/latest/experimentalに分類され、productionではspecific stable modelの利用が推奨されている。2026-07-01時点では、モデル一覧ページの最終更新は2026-06-30 UTCであり、`Gemini 3.5 Flash` と `Gemini 3.1 Flash-Lite` がGemini 3系stableとして掲載されている。

## 毎セッション開始時の確認

1. 公式Docsを確認する。
   - Gemini models: https://ai.google.dev/gemini-api/docs/models
   - Gemini context caching: https://ai.google.dev/gemini-api/docs/caching
2. モデル一覧の最終更新日、stable/preview/deprecatedの差分を確認する。
3. 差分がある場合は `data/gemini_model_policy.json` を更新する。
4. `latest` alias、preview、deprecatedの扱いをWBS/課題/QAへ反映する。
5. 監査を実行する。

```powershell
python scripts/audit_gemini_model_policy.py
```

## モデル変更の手順

1. `data/gemini_model_policy.json` の `production_default` を変更候補へ更新する前に、T780の評価Issueを作る。
2. 候補モデルを `evaluation_only_models` に入れ、production defaultは変更しない。
3. サンプル入力で以下を比較する。
   - 営業メール抽出精度
   - マッチング根拠の妥当性
   - JSON schema準拠率
   - latency
   - API cost
   - rate limit / quota
   - safety block / retry / fallback発生率
4. `exports/` に評価ログを残し、個人情報・secret・実メール全文は保存しない。
5. QA表へ「なぜ切り替える/切り替えないか」を記録する。
6. Go/No-Goで承認された場合のみ、`production_default` とアプリ既定値を同じコミットで変更する。
7. `scripts/audit_gemini_model_policy.py`、対象pytest、public demo guardを通す。

## 監査対象

| 対象 | 検査内容 |
| --- | --- |
| `src/app.py` | `GEMINI_MODEL` の既定値が `data/gemini_model_policy.json` の `production_default` と一致すること |
| `src/`, `scripts/`, `.github/` | 具体モデルIDがstable許可リスト、評価専用リスト、ブロックパターンのどれに該当するか |
| `docs/AI_SAAS_SERVICE_FREEZE_RUNBOOK.md` | 現行/既定/固定として古いモデル名を正本化していないこと |
| `data/WBS.tsv`, `data/qa_tracker.tsv` | Sheets同期される正本に古い現行モデル名が残っていないこと |

## 今回の反映

- `src/app.py` の既定値は `gemini-3.5-flash` であることを確認した。
- `src/sales_email_parser.py` と `scripts/parse_sales_emails.py` の直書き `gemini-2.5-flash` をやめ、`GEMINI_MODEL` 環境変数と `gemini-3.5-flash` 既定値に統一した。
- T848の凍結Runbook、WBS、QA表に残っていた「現行実装は `gemini-2.5-flash`」という古い正本記述を更新する。
- 監査スクリプトとpytestを追加し、次回以降のモデル名ズレを自動検出できる状態にした。

## 完了条件

T769は以下を満たしたら完了とする。

- `data/gemini_model_policy.json` が存在する。
- `scripts/audit_gemini_model_policy.py` が `status=ok` の監査証跡を出力する。
- `src/app.py` と営業メールパーサーの既定モデルが `gemini-3.5-flash` に統一されている。
- `docs/AI_SAAS_SERVICE_FREEZE_RUNBOOK.md`、`data/WBS.tsv`、`data/qa_tracker.tsv` に古いモデルを現行既定として扱う記述が残っていない。
- `docs/WBS.md` が `data/WBS.tsv` から再生成されている。

## T780 本番切り替え手順（rollout / rollback）

T769で標準化した方針に基づき、T780としてモデル移行テストと本番切り替え手順を確定した。移行評価ハーネスは `scripts/evaluate_gemini_model_migration.py`、証跡は `exports/gemini_model_migration_eval.{json,md}`。

### 2026-07-07 移行判定

- 公式Docs（models一覧・最終更新 2026-06-30 UTC）を再確認し、`Gemini 3.5 Flash` と `Gemini 3.1 Flash-Lite` がGemini 3系stable、`Gemini 2.0 Flash / 2.0 Flash-Lite` は **Shut down** であることを確認した。
- 本番既定は **`gemini-3.5-flash` を維持**する（stable最上位・シャットダウン対象外）。シャットダウン済み2.0系は `blocked_model_patterns` で拒否される。
- 移行評価ハーネスの10仮説はすべてPASS。構造化出力契約（`response_schema=EmailParseResultJSON`）はモデル非依存で、候補stableモデル間で互換であることを確認した。
- 精度/latency/costのライブ比較は `GEMINI_API_KEY` を設定して `--live` で取得する。本番相当の実値取得は運用者/Codexレーンが実施し、結果を本Runbookとexportsへ追記する。

### rollout 手順（本番切り替え時）

1. 候補モデルを `data/gemini_model_policy.json` の `evaluation_only_models` に入れ、`production_default` は変更しない。
2. `python scripts/evaluate_gemini_model_migration.py --live`（`GEMINI_API_KEY` 設定）で精度・latency・cost・schema準拠を候補モデル横断で取得する。
3. QA表へ「なぜ切り替える/切り替えないか」を記録し、Go/No-Goで承認を得る。
4. 承認後、`data/gemini_model_policy.json` の `production_default`、`src/app.py` の `GEMINI_MODEL` 既定値、`src/sales_email_parser.py` の `DEFAULT_GEMINI_MODEL` を **同一コミット**で更新する（本番既定値の黙示的なズレを防ぐ）。
5. `python scripts/audit_gemini_model_policy.py`、`python scripts/evaluate_gemini_model_migration.py --fail-on-attention`、対象pytest、`python scripts/verify_public_demo.py` を通す。
6. デプロイ後、`GEMINI_MODEL` を一時的に環境変数で新モデルへ向けたカナリア確認を行う（コード既定は据え置きのまま検証可能）。

### rollback（ロールバック）手順（切り替え後に問題が出た場合）

1. まず環境変数 `GEMINI_MODEL` を直前の安定モデル（例: `gemini-3.5-flash`）へ設定し、再デプロイなしで即時に挙動を戻す（H4で上書き反映を検証済み）。
2. 恒久復旧はコード既定値・`production_default` を旧モデルへ戻す**同一コミット**のrevertで行う。
3. `GEMINI_API_KEY` 未設定/API失敗時はdeterministic fallbackが自動的に受け皿となるため、モデル起因の全面停止は発生しない（H6で検証済み）。
4. rollback事由と再発防止をQA表・課題管理表へ記録する。

## 公式ドキュメント確認メモ

- Google Gemini models: https://ai.google.dev/gemini-api/docs/models
- Google Gemini context caching: https://ai.google.dev/gemini-api/docs/caching
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- OpenAI Codex / AGENTS.md / best practices / MCP: https://developers.openai.com/codex
- Anthropic Claude Code overview / memory / settings / security: https://code.claude.com/docs/en/overview
- GitHub Actions: https://docs.github.com/actions
