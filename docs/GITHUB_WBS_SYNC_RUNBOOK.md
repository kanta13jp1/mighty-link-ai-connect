# GitHub Issues / Project WBS 同期 Runbook

更新日: 2026-07-13  
関連WBS: T893  
正本: `data/WBS.tsv`

## 目的

各開発セッションで完了・更新したWBSタスクを、GitHub IssuesとProject #1 `Mighty Skill-Bridge`へ安全かつ冪等に同期する。公開リポジトリへWBSの長文詳細やsecretを複製せず、タスクID、概要、担当、実行レーン、状態、予定日、正本リンクだけを公開する。

## 安全設計

- 同期対象のWBS IDを引数で明示する。履歴319件以上を暗黙に一括公開しない。
- 既存IssueはタイトルのWBS IDまたは管理マーカーで照合し、人間が書いた本文を保持する。
- スクリプト管理範囲は `<!-- mighty-link-wbs:TXXX:start -->` と `...:end` の間だけとする。
- 片側だけの壊れたマーカー、同じWBS IDの重複Issue、未知のWBS ID、Project必須フィールド欠落では変更前に停止する。
- `data/WBS.tsv` の `Sheets Live 連携アクション` はGitHubへ転記しない。OAuth token、API key、メール本文、個人連絡先も転記しない。

## 状態マッピング

| WBS | GitHub Issue | Project Status |
| --- | --- | --- |
| 未着手 | Open | Todo |
| 実行中 | Open | In Progress |
| 完了 | Closed (completed) | Done |

Projectの `Start date` と `Target date` はWBSの開始日・終了予定日に合わせる。

## 実行手順

最初にdry-runし、対象IDと予定アクションを確認する。

```powershell
python scripts/sync_wbs_to_github.py T893 --dry-run
```

問題がなければ実同期し、JSON証跡を保存する。

```powershell
python scripts/sync_wbs_to_github.py T893 --report exports/github_wbs_sync_report.json
```

複数タスクは同じコマンドへ列挙する。

```powershell
python scripts/sync_wbs_to_github.py T888 T889 T890 T891 T892 T893 --report exports/github_wbs_sync_report.json
```

## セッションcloseout順序

1. `data/WBS.tsv` と必要な課題管理表・QA表を更新する。
2. `python scripts/generate_wbs_md.py` と関連テストを実行する。
3. GitHub同期をdry-runし、実同期する。
4. 作成されたIssue番号をトラッカーとWBS証跡へ反映し、同じIDを再同期する。
5. Sheets、Calendar、NotebookLM、公開デモガードを実行する。
6. 意図した差分だけをcommitし、main/masterを同期する。

## 検証

```powershell
python -m pytest tests/test_sync_wbs_to_github.py -q
gh issue list --repo kanta13jp1/mighty-link-ai-connect --state all --limit 20 --json number,title,state,projectItems
gh project item-list 1 --owner kanta13jp1 --limit 200 --format json
```

同じコマンドを再実行し、`actions` が空ならIssue本文、状態、Projectフィールドにドリフトはない。

## 復旧

- `gh auth status` が失敗する場合は同期を止め、`repo` と `project` scopeを持つ正しいGitHubアカウントで再認証する。
- Issue作成後にProject更新が失敗した場合は、同じWBS IDで再実行する。Issueは再作成せず不足フィールドだけを補う。
- WBS状態を誤って同期した場合は、GitHubを直接直すのではなく `data/WBS.tsv` を修正して再同期する。
