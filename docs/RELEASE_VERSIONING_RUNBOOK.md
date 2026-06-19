# リリースノート・バージョニング運用Runbook

作成日: 2026-06-19  
対象: Mighty-Link AI Connect / Mighty Skill-Bridge  
関連WBS: T806  
関連Issue: #113  

## 目的

Mighty-Link AI Connectのリリース履歴を、`CHANGELOG.md`、SemVer形式の`VERSION`、Git tag、GitHub Releases、WBS/Sheets/Calendar/NotebookLMの同期で一貫管理する。

本Runbookは、管理下デモ、社内確認、一般公開、有償ローンチを混同しないため、T746のGo/No-Go判定と必ず接続する。

## バージョン方針

| 種別 | 形式 | 例 | 用途 |
| --- | --- | --- | --- |
| 管理下デモ | `MAJOR.MINOR.PATCH-controlled-demo.N` | `0.1.0-controlled-demo.1` | CEO説明、社内限定確認、非GAの安定点 |
| 公開候補 | `MAJOR.MINOR.PATCH-rc.N` | `1.0.0-rc.1` | public_paid_launchの最終候補 |
| 一般公開/有償ローンチ | `MAJOR.MINOR.PATCH` | `1.0.0` | CEO/法務/開発責任者承認後のGA |
| 緊急修正 | `MAJOR.MINOR.PATCH` | `1.0.1` | 本番障害やセキュリティ修正 |

タグ名は常に `v` prefix を付ける。例: `v0.1.0-controlled-demo.1`。

## 初回リリース境界

2026-06-19時点の初回タグは `v0.1.0-controlled-demo.1` とする。これは管理下デモ用のプレリリースであり、一般公開・有償ローンチではない。

T746の現判定は次の通り。

- `controlled_demo`: GO
- `public_paid_launch`: NO_GO

したがって、GitHub Releasesでは `--prerelease` を付ける。`latest`相当やGA表現は使わない。

## 更新対象

1. `VERSION`
2. `CHANGELOG.md`
3. `docs/RELEASE_VERSIONING_RUNBOOK.md`
4. `exports/release_versioning_review.json`
5. `exports/release_versioning_review.md`
6. `data/WBS.tsv`
7. `data/issues_tracker.tsv`
8. `data/qa_tracker.tsv`
9. `data/test_results.tsv`
10. GitHub tag / GitHub Release

## リリース手順

### 1. 判定と差分確認

```powershell
python scripts/generate_production_go_no_go_review.py
python scripts/validate_release_versioning.py --expected-version 0.1.0-controlled-demo.1
git status --short --branch
```

`public_paid_launch` が `NO_GO` の場合は、タグ名またはRelease本文に `controlled-demo` や `rc` を含め、GitHub Releaseはprereleaseにする。

### 2. 変更内容の記録

- ユーザーに見せる変更は `CHANGELOG.md` に書く。
- 内部運用だけの変更はRunbookやWBSに残す。
- secret、OAuth token、DB接続文字列、Slack webhook、Stripe key、Supabase service role keyは書かない。

### 3. 検証

```powershell
python -m pytest tests/test_release_versioning.py -q
python -m pytest -q
python scripts/verify_google_workspace_account.py
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

docs変更がある場合はNotebookLM/Drive同期も行う。

### 4. commit / push / tag / GitHub Release

```powershell
git add VERSION CHANGELOG.md docs/RELEASE_VERSIONING_RUNBOOK.md exports/release_versioning_review.* data/WBS.tsv docs/WBS.md
git commit -m "chore(T806): establish release versioning workflow"
git push origin main
git push origin main:master
git tag -a v0.1.0-controlled-demo.1 -m "v0.1.0 controlled demo prerelease"
git push origin v0.1.0-controlled-demo.1
gh release create v0.1.0-controlled-demo.1 --title "v0.1.0 controlled demo prerelease" --notes-file exports/release_versioning_review.md --prerelease
```

タグはコミット後に作成し、`main`と`master`が同じcommitを指すことを確認してから発行する。

### 5. クローズアウト同期

- WBS/Sheets: `T806`を完了にする。
- Calendar: 完了済みT806イベントを削除する。
- GitHub Issue: #113をcloseし、Project #1をDoneにする。
- NotebookLM/Drive: docsと生成物を同期する。

## GitHub Release本文テンプレート

```markdown
# v0.1.0 controlled demo prerelease

This is a controlled-demo prerelease for CEO/internal review.

## Scope

- controlled_demo: GO
- public_paid_launch: NO_GO

## Highlights

- Custom domain and Firebase-managed HTTPS baseline.
- Sales-email AI matching MVP foundations through human review.
- Company account migration preparation.
- Release governance, rollback, monitoring, and support operations.

## Validation

- pytest
- WBS/Sheets/Calendar synchronization
- Public demo guard
- NotebookLM/Drive synchronization

## Boundary

This release is not a public paid launch.
```

## 公式ドキュメント確認メモ

- GitHub Releasesは、タグに紐づくプロジェクト履歴をリリースページとして公開でき、リリース作成時に新規タグ作成または既存タグ指定ができる。
- GitHub Releasesはprereleaseとして作成できるため、`public_paid_launch`がNo-Goの状態でも管理下デモの証跡として使える。
- GitHub Actions secretsはGitHub Releases本文やCHANGELOGへ出さず、Secrets/Environment secrets側で管理する。
- SemVer 2.0.0では、`MAJOR.MINOR.PATCH`を基本とし、ハイフン以降のpre-release識別子を使用できる。

## 参照

- [GitHub Docs: About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [GitHub Docs: Managing releases in a repository](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [GitHub Docs: Using secrets in GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [PRODUCTION_GO_NO_GO_CHECKLIST.md](PRODUCTION_GO_NO_GO_CHECKLIST.md)
