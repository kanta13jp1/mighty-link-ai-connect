# Mighty Skill-Bridge 月次品質レポート: 2026年06月

> [!NOTE]
> 月中時点の中間スナップショットです（生成日: 2026-06-21）。確定版は翌月 1 日に再生成します（T767 スケジュール）。

**作成日**: 2026-06-21
**作成者**: 梅澤 寛太（+ Claude Code, scripts/generate_monthly_quality_report.py による自動生成）

---

## 1. WBS 進捗

| 指標 | 今月 | 先月比 |
| :--- | :--- | :--- |
| 当月完了タスク数 | 124 件 | +25 件 |
| 全体完了率 | 89.6% (223/249) | — |
| 期限超過の未完了タスク | 3 件 | — |

**期限超過タスク（要リスケまたは着手）:**

- T745 サービス利用規約およびプライバシーポリシー本番UIでの同意チェックボックス実装（期限 2026-06-14 / 担当 AIエージェント）
- T752 ユーザーオンボーディング / アカウント登録・アクティベーションフローの設計・実装（期限 2026-06-16 / 担当 Antigravity）
- T798 利用規約・プライバシーポリシーの法務確認と本文確定（期限 2026-06-16 / 担当 人間 + Claude）

---

## 2. サービス品質 KPI

| KPI | 今月実績 | 目標 | 判定 |
| :--- | :--- | :--- | :--- |
| テスト合格率 | 100.0% (53/53) | 100% | ✅ |
| AI 診断 API 課金実行件数 | 0 件 | コストガード内 | ✅ |
| 稼働率 / P95 / 5xx エラー率 | 未計測 | ≥99.5% / ≤3.0s / ≤0.5% | ⏳ 計測基盤整備中（T743 死活監視・T755 テレメトリ・T778 SLA ビュー） |

---

## 3. 外部 API 利用・コスト

日次利用台帳監査（`reports/daily_usage_audit_*.json`、当月 2 日分）の集計:

| プロバイダ:操作 | 課金実行 | ガード遮断 | 報告トークン |
| :--- | ---: | ---: | ---: |
| gemini_api:match | 0 | 0 | 0 |
| gemini_api:parse | 0 | 0 | 0 |
| seedance_api:generation_create | 0 | 18 | 0 |

ガードアラート: 0 件（コストガードはすべて上限内）

金額ベースの実測は [COST_REPORT_2026-06.md](COST_REPORT_2026-06.md) を参照（GCP Billing API 連携は T757 週次コストダッシュボードで自動化予定）。

---

## 4. インシデント・課題（当月起票/更新）

| ID | 重要度 | 状態 | タイトル |
| :--- | :--- | :--- | :--- |
| R10 | MED | resolved | 公開 URL の外部漏洩 (方向性 A/C 選択時) |
| HANDOFF-4 | MED | resolved | scripts/sync_docs_to_notebooklm.py に Gemini explicit context caching 導入 |
| HANDOFF-5 | LOW | resolved | Codex skills packaging (/sync-wbs, /sync-notebooklm, /verify-demo) |
| HANDOFF-15 | LOW | resolved | scripts/generate_ceo_presentation_deck.py に --style canva-export オプション追加 |
| HANDOFF-25 | LOW | resolved | Figma wireframe ファイルへの MCP 流し込み (rate limit 解除待ち) |
| R28 | HIGH | open | 経歴書のマスキング法務合意確認 |
| R29 | MED | resolved | APIコストの月額制限の検証 |
| R30 | LOW | open | 録画データの整理 |
| R31 | MED | open | 既存診断ツールの選定調査 |
| R32 | HIGH | open | AI適性状況診断ツールの実装 |
| R33 | HIGH | open | 勤務表データの自動解析実装 |
| R34 | MED | open | 開発マイルストーンの策定 |
| R35 | MED | open | APIコストの月額制限の検証 |
| R36 | HIGH | open | 経歴書と心理データの法務合意確認 |
| R37 | HIGH | open | Firebase ホスティング デプロイの認証情報およびターゲット設定エラー |
| R38 | MED | resolved | Firebase main/master 同時デプロイ競合による Cloud Functions 更新失敗 |
| R39 | HIGH | resolved | Firebase Functions invoker IAM 権限不足による CI 失敗 |
| R40 | MED | resolved | WBS タスクID重複（T774/T775 二重定義）による誤完了フラグ |
| R41 | HIGH | resolved | 認証なし DB 診断エンドポイント /api/db-test の露出 |
| R42 | MED | resolved | GitHub Actions Node 20 action runtime deprecation warnings |
| R43 | MED | resolved | GitHub Project item追加 API が 401 を返す |
| R45 | HIGH | resolved | Firebase/Supabase staging と production の接続情報混在リスク |
| R44 | HIGH | resolved | 本番 /api/* 全エンドポイント 502/504（Cloud Functions 全リクエストハング） |
| R46 | MED | resolved | 比較ボード「詳細分析」がスキルカテゴリ名と定型文を /api/match へ送信し無意味な診断を生成 |
| R47 | LOW | resolved | deterministic fallback の QA 質問テンプレートにプレースホルダ文が混入 |
| R48 | HIGH | open | 利用規約・プライバシーポリシー初版の法務確認待ち |
| R49 | HIGH | resolved | starlette 0.52.1 に CVE-2026-48710（Host ヘッダ未検証による request.url パス乖離） |
| R50 | MED | resolved | Google API 呼び出し 17 箇所で requests timeout 未指定（bandit B113） |
| R51 | MED | open | 特商法表記の事業者情報・販売価格の確定待ち |
| R52 | LOW | resolved | FastAPI @app.on_event("startup") が deprecated（lifespan ハンドラへ移行要） |
| R53 | MED | open | Supabase Postgres 14 サポート終了 (2026-07-01) — 本番/staging プロジェクトの PG バージョン未確認 |
| R54 | HIGH | resolved | ml-mightylink.com の Cloud DNS ゾーン所有アカウント不明 — T740 カスタムドメイン CNAME 追加がブロック |
| R55 | MED | resolved | Public Demo Guard workflow が requests 未インストールで失敗 |
| R56 | MED | resolved | R44本番502障害のポストモーテム運用が未整備 |
| R57 | MED | resolved | 本番ログローテーションとアクセスログ保持運用が未整備 |
| R58 | MED | resolved | 定期パフォーマンス診断とDBインデックス最適化運用が未整備 |
| R59 | MED | resolved | 本番死活監視とSlackアラート運用が未整備 |
| R60 | MED | resolved | サードパーティAPIキー・Webhook secretのローテーション運用が未整備 |
| R61 | MED | resolved | API レート制限未適用による高コストAPI連打・認証経路総当たり・DDoS増幅リスク |
| R62 | MED | resolved | DB migration管理がアプリDDL・Supabase migration・運用docsに分散していた |
| R63 | MED | resolved | CPU/メモリ/ディスク/DBクエリ/外部API/URL到達性の監視情報が個別レポートに分散していた |
| R64 | MED | resolved | 週次コスト配賦と通知が手動レポート・個別コンソール確認に分散していた |
| R65 | MED | resolved | Firebase Functions / Cloud Run から Supabase へ毎回直接接続する実装が残っていた |
| R66 | MED | resolved | mightylink-app.com のSSL証明書発行待ちにより販売URL確定が保留されていた |
| R67 | MED | resolved | ローカルFirebase/Supabase開発環境の検証基盤が未整備 |
| R68 | MED | resolved | Supabase Query Performance / Index Advisor の定例レビュー証跡が未整備 |
| R69 | MED | resolved | Firebase/Supabaseのクォータ・エラー・課金・DB飽和アラート設計が個別Runbookに分散していた |
| R70 | MED | resolved | 診断結果の役立ち度/NPSを継続収集する仕組みが未整備だった |
| R71 | MED | resolved | ユーザー問い合わせ窓口と対応SLAが未整備だった |
| R72 | MED | resolved | 6/18 Gemini CLI / Code Assist 個人向け停止に伴う残存依存リスク |
| R73 | MED | resolved | 本番Go/No-Go判定基準と承認プロセスが未整備だった |
| R74 | HIGH | open | WordPress/FTP経由の既存サイト更新で全ファイル置換や認証情報記録が発生するリスク |
| R75 | HIGH | open | 営業メールAIマッチングの個人情報・誤抽出・誤マッチングリスク |
| R76 | MED | resolved | 個人アカウントで構築したGitHub/Firebase/Supabase/AI開発ツールの会社移管リスク |
| R77 | MED | resolved | Geminiメモと文字起こしで次回日程・マッチング方向の解釈に差分があった |
| R78 | MED | resolved | 営業メール取り込みPoCで本文全文・認証情報がレポートへ混入するリスク |
| R79 | HIGH | resolved | モバイル表示時にホームページで main1.jpeg の 404 エラーが発生する問題 |
| R80 | HIGH | resolved | 営業メールAIマッチングDBを匿名RESTから直接読書きできるリスク |
| R81 | HIGH | resolved | 営業メールAI抽出結果に本文全文・個人連絡先・secret-like値が混入するリスク |
| R82 | HIGH | resolved | 営業メールAIマッチング候補リストに非公開本文・連絡先・未レビュー判断が混入するリスク |
| R83 | MED | resolved | 営業メールAIマッチングの人間レビューコメントに連絡先やsecret-like値が混入するリスク |
| R84 | MED | resolved | リリースタグと一般公開/有償ローンチ判定が混同されるリスク |
| R85 | MED | resolved | ユーザーデータのセルフエクスポートが未整備でEOL/移行/開示請求時に手作業へ依存するリスク |
| R86 | MED | resolved | 営業メール自動取り込み方式をGmail前提で決め打ちして実装するリスク |
| R87 | HIGH | resolved | Google Workspace OAuth token失効でSheets/Calendar/Drive同期が止まるリスク |
| R88 | MED | resolved | NotebookLM ask生成・既存source refreshの長時間化でdocs同期closeoutが止まるリスク |
| R89 | MED | resolved | 毎セッションの公式Docs確認対象が多く、三ツール運用ゲートと同期手順が分散するリスク |
| R90 | MED | resolved | Supabase PG14 EOL確認時にDB URLやversion確認ログを安全に扱うゲートが未整備 |
| R91 | MED | resolved | Stripe Customer Portal 実装時にlive key未設定・ID露出・外部通信誤実行が起きるリスク |
| R92 | MED | resolved | NotebookLM docs/source同期スクリプトがskip/drive-onlyでも5分タイムアウトする |
| R93 | MED | open | 月次品質レポートのNotion/Slack本送信はGitHub Secrets設定に依存する |

**セキュリティ検出（security_log）:**

- SEC-004 [HIGH] bandit B324: Calendar syncKey 生成に SHA1 を使用（弱ハッシュ警告） — FIXED
- SEC-005 [HIGH] pip-audit: CVE-2026-48710 Host ヘッダ未検証による request.url パス乖離（パス認可バイパスの可能性） — FIXED
- SEC-006 [MED] bandit B113: requests timeout 未指定 17 箇所（sync スクリプト無期限ハングリスク） — FIXED
- SEC-007 [LOW] bandit B310 urlopen scheme / B108 hardcoded /tmp — FIXED

---

## 5. 翌月（または直近）の優先アクション

1. T791 Stripe Billing Meters API を用いた課金実装・Webhook 検証・本番適用（開始 2026-07-01 / 担当 Codex）
2. T782 アクセス増加に伴うデータベース接続負荷分散（リードレプリカ・プールサイズ最適化）の設計と負荷テスト検証（開始 2026-07-02 / 担当 Codex）
3. T819 7/2(木)仮 定例打ち合わせの実施と進捗報告（開始 2026-07-02 / 担当 寛太梅澤）
4. T800 利用状況アナリティクス計測設計と導入（イベント計測・KPI集計）（開始 2026-07-03 / 担当 Codex）
5. T769 Gemini API モデルバージョン追従および新モデル移行プロセスの標準化（開始 2026-07-04 / 担当 Codex + Claude）

---

## 6. 参照リンク

- [WBS スプレッドシート](https://docs.google.com/spreadsheets/d/1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8)
- [GitHub リポジトリ](https://github.com/kanta13jp1/mighty-link-ai-connect)
- [公開デモ URL](https://kanta13jp1.github.io/mighty-link-ai-connect/)
- [SLA/KPI 定義](../../SLA_KPI_DEFINITION_AND_MEASUREMENT.md) / [レポート仕様 (T767)](../../MONTHLY_PROGRESS_REPORT_AND_KPI_DASHBOARD.md)
