# ポストモーテム: 本番 /api/* 502/504 障害 (2026-06-11)

## 概要

- Incident ID: R44
- Severity: P2
- Status: resolved
- 検知日時: 2026-06-11 JST
- 復旧日時: 2026-06-11 JST
- MTTR: 同日復旧
- 影響範囲: Firebase Hosting 経由の `/api/*` が 502、Cloud Run 直URLが 504
- 関連WBS: T795 / T796 / T810
- 関連GitHub Issue: #84
- 関連Runbook: [INCIDENT_POSTMORTEM_RUNBOOK.md](INCIDENT_POSTMORTEM_RUNBOOK.md), [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md)

## タイムライン

| 時刻 | 出来事 | 担当 | 証跡 |
| --- | --- | --- | --- |
| 2026-06-11 | Firebase Hosting 経由 `/api/*` の 502 と Cloud Run 直URL 504 を確認 | Claude Code | `data/issues_tracker.tsv` R44 |
| 2026-06-11 | `main.py` の import 時 ASGIMiddleware 生成と gunicorn fork の不整合を特定 | Claude Code | `docs/MULTI_AI_WORKFLOW.md` Refresh |
| 2026-06-11 | ASGIMiddleware を初回リクエスト時の遅延生成へ変更 | Claude Code | `main.py` |
| 2026-06-11 | `firebase deploy --only functions` の手動デプロイで復旧 | Claude Code | R44 メモ |
| 2026-06-13 | 本ポストモーテムと標準運用をT810で整備 | Codex | `docs/INCIDENT_POSTMORTEM_RUNBOOK.md` |

## 影響

- ユーザー影響: 本番 API 全体が利用不可。診断、保存、管理APIが応答しない可能性。
- データ影響: 既知のデータ破損なし。
- 課金影響: 当時はStripe本番課金前のため直接影響なし。
- セキュリティ影響: 既知の情報漏洩なし。
- CEO共有URL / 販売URLへの影響: GitHub Pages の静的デモは継続利用可能。本番API利用フローのみ影響。

## 根本原因

### 技術原因

`main.py` が import 時に `a2wsgi.ASGIMiddleware` を生成していた。本番 runtime は `functions-framework -> gunicorn` で、マスタープロセスが app をロードした後に worker を fork する。import 時に起動した a2wsgi のイベントループスレッドは worker へ引き継がれず、リクエスト処理が `run_coroutine_threadsafe().result()` で永久ブロックした。

### 運用原因

ローカル Flask dev server と Firebase Emulator は fork しないため、受入テストでは再現しなかった。また、CIでは Functions deploy が無効化されており、本番Functionsの実行形態を自動検証できていなかった。

### なぜ事前検知できなかったか

- fork後workerでのASGI bridge初期化を検証するテストが無かった。
- 本番 `/api/*` の監視・エラー通知がまだT743/T755の未完了範囲だった。
- Functions deploy が手動で、deploy後の自動smoke testが不足していた。

## 対応

### 緩和策

- `main.py` のASGIMiddleware生成を初回リクエスト時へ遅延。
- workerプロセス内でイベントループスレッドを起動するよう修正。
- 手動Functions deployで復旧。

### 恒久対応

| ID | アクション | 状態 | 連携先 |
| --- | --- | --- | --- |
| R44 | ASGIMiddleware遅延生成と本番復旧 | resolved | T795 / T796 |
| T795 | Supabase transaction pooler切替と本番DB接続安定化 | 完了 | `docs/MULTI_AI_WORKFLOW.md` |
| T796 | CI Functions deploy環境変数保護とdeployゲート解除 | 完了 | `.github/workflows/deploy.yml` |
| T810 | ポストモーテム標準運用整備 | 完了 | 本書 |
| T743/T755 | 本番死活監視・監視ダッシュボード | 未着手 | WBS |

## 復旧後検証

- Firebase Hosting標準デモURLの公開確認
- `/api/*` の応答確認
- R44を `data/issues_tracker.tsv` に記録
- 後続対応をT795/T796へ分離

## 再発防止アクション

| ID | アクション | オーナー | 期限 | 連携先 |
| --- | --- | --- | --- | --- |
| R44 | 本番502/504の原因・緩和・恒久対応を課題管理表へ記録 | Claude Code | 2026-06-11 | `data/issues_tracker.tsv` |
| R56 | R44のポストモーテム化と記録ルール整備 | Codex | 2026-06-13 | T810 / Issue #84 |
| T743 | 本番環境の死活監視とSlack連携アラート | Codex | 2026-06-15 | WBS |
| T755 | テレメトリ/リソース監視ダッシュボード | Codex | 2026-06-20 | WBS |

## 学び

- 本番runtimeのプロセスモデルは、ローカル/Emulatorの通過だけでは保証できない。
- 本番APIの障害は、静的デモが正常でもCEO共有体験に影響しうるため、API smoke testをGo/No-Go条件に含める。
- 復旧記録は `MULTI_AI_WORKFLOW.md` だけでなく、課題管理表とポストモーテムに分離して残す。

## クローズ条件

- [x] 課題管理表へ反映した
- [x] GitHub Issue / Projectへ反映する
- [x] WBSへ反映する
- [x] 関連Runbookを更新する
- [x] 復旧後検証を記録した
