# プロジェクト構成方針

Mighty-Link AI Connect は、ローカル Web アプリ、Google API 連携スクリプト、設計ドキュメント、同期データが同居するプロジェクトです。ファイル数が増えてきたため、以下の責務で整理します。

## 現在の構成

```text
mighty-link-ai-connect/
├── src/          # FastAPI とフロントエンド
├── scripts/      # Google API 同期・共有・公開デモ検証などの運用スクリプト
├── .github/      # GitHub Actions による公開デモ保護
├── docs/         # 要件、設計、手順、作業ログ
├── data/         # 同期元データ、ローカル監査ログ
├── exports/      # 生成ファイル、外部取り込み用ファイル
├── requirements.txt
├── credentials.json.template
└── README.md
```

## 配置ルール

| 種別 | 配置先 | 例 |
| --- | --- | --- |
| アプリ本体 | `src/` | `app.py`, `index.html` |
| 運用スクリプト | `scripts/` | `sync_wbs_to_calendar.py`, `share_resources.py`, `verify_public_demo.py` |
| CI ガード | `.github/workflows/` | `public-demo-guard.yml` |
| 仕様・手順 | `docs/` | `SETUP_GUIDE.md`, `BACKEND_AI_PIPELINE.md`, `CEO_PRESENTATION_PREP_2026-06-02.md`, `requirements.md`, `database.md` |
| 同期元データ | `data/` | `WBS.tsv` |
| 実行時監査ログ | `data/audit/` | `.gitkeep`, `ai_audit.jsonl` (Git 管理対象外) |
| 生成物 | `exports/` | `mighty_development_plan.ics` |
| 認証情報 | ルート直下 | `client_secret.json`, `authorized_user.json` |

## 認証ファイルの扱い

以下はプロジェクトルート直下に置きます。スクリプトと FastAPI サーバーはこの前提で参照します。

- `client_secret.json`
- `credentials.json`
- `authorized_user.json`

これらは `.gitignore` の対象です。テンプレートとして共有する場合は `credentials.json.template` のようなダミー値のファイルだけを使います。

## 今後の拡張候補

- `tests/`: API と同期スクリプトの自動テストを追加する場合。
- `assets/`: 画像、ロゴ、サンプル PDF などを追加する場合。
- `config/`: 共有先メール、スプレッドシート ID、カレンダー名を外部設定化する場合。
- `logs/`: 手動実行ログを保存したい場合。ただし Git 管理対象にはしない。
- `data/audit/`: API 判定ログの置き場。`.jsonl` は Git 管理せず、`.gitkeep` だけでディレクトリを維持する。

## 実行コマンド

```powershell
python src/app.py
python scripts/verify_public_demo.py
python scripts/sync_wbs_to_calendar.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/share_resources.py
```
