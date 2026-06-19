# 本番リリース Go/No-Go 判定チェックリスト (T746)

作成日: 2026-06-17
オーナー: VSCode + Codex レーン
関連: [WBS.md](WBS.md) / [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md) / [PRODUCTION_DOMAIN_SETUP_GUIDE.md](PRODUCTION_DOMAIN_SETUP_GUIDE.md)

---

## 目的

T746 は、Mighty-Link AI Connect を本番公開または有償提供へ進める前に、判定基準・証跡・承認者・未完了ゲートを一元化するためのタスクである。

本チェックリストでは、次の2つを明確に分ける。

- `controlled_demo`: CEO共有済みの管理下デモ、社内確認、限定説明に使える状態
- `public_paid_launch`: 一般ユーザー向け公開、有償プラン開始、Stripe課金を含む状態

---

## 現時点の判定

| Scope | 判定 | 理由 |
| --- | --- | --- |
| `controlled_demo` | `GO` | GitHub Pages公開デモ、本番URL、問い合わせ窓口、DR/Incident/Rollback、監視・クォータRunbookの証跡が揃っている |
| `public_paid_launch` | `NO_GO` | 法務/CEO承認、規約同意UI、オンボーディング、法定4ページ実装、Stripe課金、負荷テスト、営業メールAIマッチング本番hardeningが未完了 |

つまり、現状は「社長説明・限定デモは継続可。一般公開・有償ローンチは未承認」である。

2026-06-17の小林社長・梅澤打ち合わせで、共有営業アドレスに毎日約1,000通届く営業メールから案件要件や要員情報を抽出し、エンジニア候補と照合するAIマッチング機能が最優先開発項目になった。文字起こし照合では、エンジニア/経歴書から案件を探す方向に加えて、案件要件から候補人材を探す逆方向も要望として確認した。これに伴い、営業メールAIマッチングMVPは `public_paid_launch` の追加ゲートとして扱う。T817_6までで安全な取り込みPoC、DB/RLS、抽出、候補検索、人間レビュー保存は完了した。限定デモのGo判定は維持するが、本機能を売りにした一般公開、有償提供、営業利用はT817_7の実メール接続後hardening完了後に再判定する。

---

## 正本と生成物

| 種別 | パス / 同期先 | 用途 |
| --- | --- | --- |
| 判定基準TSV | [../data/release_go_no_go_criteria.tsv](../data/release_go_no_go_criteria.tsv) | Go/No-Go基準の正本 |
| 自動レビュー | [../scripts/generate_production_go_no_go_review.py](../scripts/generate_production_go_no_go_review.py) | TSVとWBSを突合し、判定レポートを生成 |
| Markdown証跡 | [../exports/production_go_no_go_review.md](../exports/production_go_no_go_review.md) | 人間レビュー用 |
| JSON証跡 | [../exports/production_go_no_go_review.json](../exports/production_go_no_go_review.json) | CI/自動処理用 |
| Google Sheets | `リリース判定` タブ | WBS/課題/QAと同じスプレッドシートへ同期 |

WBSの正本は [../data/WBS.tsv](../data/WBS.tsv) であり、[WBS.md](WBS.md) は `scripts/generate_wbs_md.py` で再生成する。

---

## 判定ルール

| 状態 | 意味 | リリース判断 |
| --- | --- | --- |
| `PASS` | 証跡があり、要求状態を満たしている | Go要件を満たす |
| `WARNING` | 進行可能だが注意点が残る | Go with warnings |
| `HUMAN_GATE` | CEO、法務、開発責任者など人間承認が必要 | 承認完了までNo-Go |
| `BLOCKED` | 必須タスクまたは証跡が未完了 | No-Go |
| `N/A` | 対象外 | 判定から除外 |

`public_paid_launch` は、`BLOCKED` が0件、かつ `HUMAN_GATE` が承認済みになるまで `NO_GO` とする。

---

## 未完了ゲート

| WBS | 内容 | 現在の扱い |
| --- | --- | --- |
| T745 | 利用規約・プライバシーポリシー同意チェックボックス実装 | `BLOCKED` |
| T752 | ユーザーオンボーディング / アカウント登録・アクティベーション | `BLOCKED` |
| T777 | 法定4ページ実装とフッター常時リンク | `BLOCKED` |
| T776 / T791 | Stripe課金設計・Billing Meters/Webhook検証 | `BLOCKED` |
| T770 | 同時100ユーザー想定の負荷テスト | `BLOCKED` |
| T817_7 | 共有営業メールAIマッチングMVPの個人情報/監査/負荷確認、実メール接続後の運用hardening | `BLOCKED` |
| T798 | 利用規約・プライバシーポリシー法務確認 | `HUMAN_GATE` |
| T804 | 料金プラン・価格設定のCEO承認 | `HUMAN_GATE` |

---

## 承認プロセス

1. 各レーンが担当ゲートの証跡を `docs/`、`exports/`、GitHub Issue、WBSへ残す。
2. Codexレーンが `python scripts/generate_production_go_no_go_review.py` を実行し、判定レポートを再生成する。
3. `python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8` で `リリース判定` タブへ同期する。
4. 完了済みWBSイベントは `python scripts/sync_wbs_to_calendar.py` でGoogle Calendarから削除する。
5. `public_paid_launch` の `BLOCKED` が0件になった後、CEO、法務、開発責任者が最終承認する。
6. Go判定時は、known-good commit、Firebase Hosting release、Cloud Run revision、Supabase backup/PITR時刻、rollback担当者を記録してから本番反映する。

---

## 技術前提

- レジストラ: お名前.com
- ホスティング / バックエンド: Firebase Hosting、Firebase Functions、GCP
- DB: Supabase
- ソースコード管理: GitHub
- WBS/課題/QA/リリース判定: Google Workspace Sheets

---

## 公式ドキュメント確認メモ

2026-06-17時点の確認対象:

- Firebase Hosting / Functions: https://firebase.google.com/docs/hosting / https://firebase.google.com/docs/functions
- Gmail API: https://developers.google.com/workspace/gmail/api/guides
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- GitHub Actions: https://docs.github.com/actions
- Supabase: https://supabase.com/docs/guides/getting-started
- Stripe rate limits / API運用: https://docs.stripe.com/rate-limits
- Claude Code / Codex / Gemini / Notion / Slack など、プロジェクト運用で使うAI・開発ツールの公式Docs

公式Docs確認は、判定基準そのものではなく「現在の実装・同期・運用手順が各サービスの現行ガイドに反していないか」を確認するために行う。
