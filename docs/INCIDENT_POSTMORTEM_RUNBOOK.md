# 障害インシデント対応記録・ポストモーテム運用 Runbook (T810)

作成日: 2026-06-13  
担当レーン: Claude Code / Codex  
対象: Mighty Skill-Bridge / Mighty-Link AI Connect 本番運用

## 1. 目的

本書は、本番障害や重大な品質劣化が発生したときに、原因・影響・復旧・再発防止を同じ粒度で記録し、WBS / 課題管理表 / GitHub Issues / Project へ必ず接続するための標準手順である。

T749 の DR Runbook は「発生時にどう動くか」を扱い、本書は「復旧後に何を残し、何を次の改善へ送るか」を扱う。

## 2. 公式ドキュメント確認

2026-06-13 に以下を確認した。

- Firebase Hosting custom domain / release management: 本番URL・Hosting release・rollbackの確認観点
- Supabase backups / migrations: DB障害時のbackup、PITR、migration記録の確認観点
- GitHub Projects automation: Issue close と Project Done の同期観点
- Slack developer docs: 障害通知・更新共有先の設計観点
- OpenAI / Anthropic / Google Gemini / Microsoft Foundry: AI駆動開発では、agent作業の証跡・権限・外部tool利用を残すこと
- Stripe docs: 課金障害時は sandbox / live mode とAPI versionを記録すること

## 3. 作成トリガー

次のいずれかに該当した場合、復旧から24時間以内に `docs/POSTMORTEM_YYYY-MM-DD_<ID>_<SLUG>.md` を作成する。

| 条件 | 必須度 | 例 |
| --- | --- | --- |
| P1/P2障害 | 必須 | 本番停止、データ損失、ログイン不可、課金不可 |
| 重大な本番API障害 | 必須 | `/api/*` 502/504、Cloud Run / Functions ハング |
| データ整合性・RLS・権限事故 | 必須 | 誤公開、tenant分離不備、service role誤用 |
| セキュリティ監査でHigh以上 | 必須 | secret漏洩、依存CVE、認可回避 |
| P3障害で再発可能性が高い | 推奨 | 一部機能停止、性能劣化、外部API障害 |

## 4. 記録ファイル命名

```text
docs/POSTMORTEM_YYYY-MM-DD_<ISSUE_ID>_<SHORT_TITLE>.md
```

例:

```text
docs/POSTMORTEM_2026-06-11_R44_PRODUCTION_API_502.md
```

## 5. 必須メタデータ

各ポストモーテムには以下を必ず入れる。

| 項目 | 記録内容 |
| --- | --- |
| Incident ID | 課題管理表のID。例: `R44` |
| Severity | P1 / P2 / P3 / P4 |
| Status | investigating / mitigated / resolved / monitoring |
| Detection time | 最初に検知した時刻 |
| Recovery time | ユーザー影響が解消した時刻 |
| Impact | 影響URL、API、ユーザー範囲、データ影響 |
| Root cause | 技術原因と運用原因を分けて記載 |
| What worked | 有効だった検知・調査・復旧手順 |
| What did not work | 遅延、盲点、再現不能だった点 |
| Preventive actions | 課題管理表ID、WBS ID、GitHub Issueへ接続 |
| Validation | 復旧後に実行したテスト・公開デモ確認 |

## 6. 標準テンプレート

```markdown
# ポストモーテム: <障害タイトル> (<YYYY-MM-DD>)

## 概要

- Incident ID:
- Severity:
- Status:
- 検知日時:
- 復旧日時:
- MTTR:
- 影響範囲:
- 関連WBS:
- 関連GitHub Issue:
- 関連Runbook:

## タイムライン

| 時刻 | 出来事 | 担当 | 証跡 |
| --- | --- | --- | --- |
| HH:MM | 検知 |  |  |
| HH:MM | 原因仮説 |  |  |
| HH:MM | 緩和 |  |  |
| HH:MM | 復旧確認 |  |  |

## 影響

- ユーザー影響:
- データ影響:
- 課金影響:
- セキュリティ影響:
- CEO共有URL / 販売URLへの影響:

## 根本原因

### 技術原因

### 運用原因

### なぜ事前検知できなかったか

## 対応

### 緩和策

### 恒久対応

### 復旧後検証

## 再発防止アクション

| ID | アクション | オーナー | 期限 | 連携先 |
| --- | --- | --- | --- | --- |
| Rxx |  |  | YYYY-MM-DD | WBS / GitHub Issue |

## 学び

## クローズ条件

- [ ] 課題管理表へ反映した
- [ ] GitHub Issue / Projectへ反映した
- [ ] WBSへ反映した
- [ ] 関連Runbookを更新した
- [ ] 復旧後検証を記録した
```

## 7. 課題管理表への連携ルール

再発防止アクションは `data/issues_tracker.tsv` へ必ず反映する。

- 既存課題がある場合: 該当行の `関連 docs` にポストモーテムを追加する
- 新規課題の場合: `Rxx` を採番し、`関連 WBS` と `関連 Issue` を入れる
- WBSタスクとして実装する場合: `関連 WBS` に対象IDを入れる
- 完了した場合: `状態=resolved`、`更新日` を更新する

## 8. R44 実例

本運用の初回適用例として、2026-06-11 の本番 `/api/*` 502/504 障害を [POSTMORTEM_2026-06-11_R44_PRODUCTION_API_502.md](archive/historical_reports/POSTMORTEM_2026-06-11_R44_PRODUCTION_API_502.md) に記録した。

## 9. 関連ドキュメント

- [DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
- [PRODUCTION_ROLLBACK_RUNBOOK.md](PRODUCTION_ROLLBACK_RUNBOOK.md)
- [SUPABASE_BACKUP_RESTORE_RUNBOOK.md](SUPABASE_BACKUP_RESTORE_RUNBOOK.md)
- [SLA_KPI_DEFINITION_AND_MEASUREMENT.md](SLA_KPI_DEFINITION_AND_MEASUREMENT.md)
- [SECURITY_AUDIT_RUNBOOK.md](SECURITY_AUDIT_RUNBOOK.md)
