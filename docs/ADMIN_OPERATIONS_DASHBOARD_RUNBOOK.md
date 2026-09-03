# 管理者向け統合ダッシュボード Runbook

- 対象WBS: T842
- 関連課題: R98
- 作成日: 2026-06-27
- レーン: Antigravity + Gemini / Codex / Claude Code
- 技術前提: `index.html`, FastAPI on Firebase Functions, Supabase / SQLite fallback

## 概要

T842では、診断アンケート、勤怠、営業メールAIマッチングの管理者向け統合ビューを、実データ集計APIとCSVレポート出力へ接続した。ダッシュボードは既存のT840/T841/T817_6 summary APIを再利用し、直接識別子、勤務表原本、メール本文、secret-like値を新たに出力しない。

## API

### 統合集計

`GET /api/admin/operations-dashboard?limit=20`

Basic Auth必須。レスポンスには次を含む。

- `kpis`: 診断回答数、モチベーション平均、勤怠打刻/勤務表件数、承認待ち件数、営業メールレビュー件数、レビュー完了率。
- `sources.employee_assessment`: `GET /api/employee-assessment/responses/summary` のredacted済み結果。
- `sources.attendance`: `GET /api/attendance/summary` の集計結果。
- `sources.sales_email_review`: `GET /api/sales-email/reviews/summary` のレビュー結果。
- `security`: Basic Auth、CSV出力認証、直接識別子除外、勤務表原本除外、メール本文除外、secret redactionの運用フラグ。

### CSVレポート

`GET /api/admin/operations-dashboard/report.csv?limit=100`

Basic Auth必須。KPI、部署別診断件数、勤怠ステータス、営業メールレビュー状態、securityフラグのみをCSVで出力する。匿名キーや最近の自由記述は含めず、Sheets/NotebookLMへ載せても直接識別子が混ざらない粒度にしている。

## フロントエンド

`index.html` の管理者統合ダッシュボードおよび `admin/index.html` の外部API課金ガードポータルに、管理者ユーザー名、パスワード、実データ読込、CSV export、およびSVGインタラクティブ・データビジュアル（折れ線トレンド・ドーナツ円グラフ・ツールチップ表示）を追加した。

- 認証情報はブラウザ内でBasic Authヘッダーに使うだけで、localStorageやHTMLへ保存しない。
- APIがないGitHub Pages controlled demoでは、従来の静的デモ値およびデモアニメーションSVGグラフを表示したままにする。
- APIが成功した場合のみ、診断、勤怠、営業メールレビューの表、KPI、およびSVG折れ線・ドーナツグラフを実データで上書き再描画する。
- グラフ要素（データポイント）にマウスホバーすると詳細数値を示すツールチップ（Tooltip）が表示される。

## 保存しない情報

- 社員番号、氏名、メールアドレス、電話番号などの直接識別子。
- 勤務表CSV/PDFの原本、元ファイル名、明細行。
- 営業メール本文、BP担当者の連絡先、候補者の直接連絡先。
- API key、token、password、secret-like値。

## 検証

- `tests/test_api.py::test_admin_operations_dashboard_requires_auth_aggregates_and_exports_csv`
- `python -m pytest -q`
- `python scripts/verify_public_demo.py --url https://mightylink-app.com/`

## 公式ドキュメント確認メモ

2026-06-27のセッションで、Claude Code、OpenAI Codex、Google Gemini/Workspace、Microsoft Azure AI Foundry、GitHub Projects API、Slack、Stripe Billing、Supabase、Unity、Reddit、Apple Machine Learning、MiMo、お名前.comなどの公式ドキュメントを確認した。T842には特に、Basic Auth付き管理者境界、Sheets/Calendar同期、GitHub Issues/Projects同期、Supabase RLS、redaction済み集計だけを公開する方針を反映した。
