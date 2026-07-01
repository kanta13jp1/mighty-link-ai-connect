# 課題管理表・QA表 開発ブロッカー棚卸し（T854）

- 実施日: 2026-06-27
- 担当レーン: VSCode + Codex / VSCode + Claude Code
- 関連WBS: T853, T854, T849
- 関連Issue: #141
- 関連リスク/QA: R101, QA-78, PUBLIC-15

---

## 2026-07-01 T858完了後追記

T770で新規open化した `R110` は、T858の100同時ユーザー/300リクエスト再試験により解決済みへ戻した。

再試験結果は `docs/LOAD_TEST_100_USERS_REPORT_2026-07-01.md` と `exports/load_test_100_users_2026-07-01.json` を正本とし、エラー0、全体P50 508.52ms、P95 943.81ms、P99 1155.32ms、`/api/match` P95 1133.85msでSLAを満たした。

このため、課題管理表の開発必須openは0件、QA表の未回答は0件へ復帰し、`PUBLIC-15` は `PASS` として扱う。ただし `public_paid_launch` 全体は、法務、価格、課金、Firebase CI/CD、DNS/HTTPS、実メール接続、本番UAT、会社運用引継ぎなど残ゲートがあるため引き続き `NO_GO` とする。

## 2026-07-01 追記

2026-06-27のT854時点では `PUBLIC-15` は `PASS` だったが、2026-07-01のT770負荷テストにより `R110`（100同時ユーザー負荷テストで`/api/match`のP95がSLA 3秒を超過）を新規open化した。

最新の `python scripts/audit_issue_qa_blockers.py` 実行結果は次のとおり。

| 対象 | 結果 |
| --- | --- |
| 課題行数 | 153 |
| QA行数 | 119 |
| 課題ブロッカー数 | 1 |
| QAブロッカー数 | 0 |
| 監査判定 | `blocked` |

したがって、現時点の `PUBLIC-15` はT858完了まで `BLOCKED` として扱う。T854の棚卸し結果は履歴証跡として保持するが、現在の開発完了判定は `exports/issue_qa_blocker_audit.*` と `data/release_go_no_go_criteria.tsv` を正本とする。

---

## 目的

WBS全完了時に「サイト開発完了」と宣言できるよう、Sheets正本である `data/issues_tracker.tsv` と `data/qa_tracker.tsv` を棚卸しし、未分類の開発必須open課題と未回答/未承認QAをゼロにする。

削除だけで処理せず、各行を次のいずれかへ分類した。

| 分類 | 意味 |
| --- | --- |
| `resolved` | 実装、文書化、または後続タスク完了により解決済み |
| `transferred` | 未完了の実ゲートとしてWBSまたはGo/No-Goへ移管済み |
| `accepted_non_blocker` | 開発完了の必須条件ではなく、通常保守または警告として許容 |
| `closed` | 既に閉鎖済み |

## 棚卸し前の状態

| 対象 | 状態 |
| --- | --- |
| 課題管理表 | `open` 34件 |
| QA表 | `answered` 7件、`回答済` 65件、`想定済` 39件 |

QA表の `answered` は回答済みの英語表記揺れだったため、すべて `回答済` へ正規化した。

## 棚卸し後の状態

`python scripts/audit_issue_qa_blockers.py --fail-on-blockers` を実行し、次の結果を得た。

| 対象 | 結果 |
| --- | --- |
| 課題行数 | 145 |
| QA行数 | 111 |
| 課題ブロッカー数 | 0 |
| QAブロッカー数 | 0 |
| 監査判定 | `pass` |

生成証跡:

- `exports/issue_qa_blocker_audit.md`
- `exports/issue_qa_blocker_audit.json`

## 重要な移管判断

| 課題 | 判断 |
| --- | --- |
| R99 | サイト開発完了総合判定はT849へ移管 |
| R100 | Firebase CI/CD本番デプロイ認証はT852 / PUBLIC-14へ移管 |
| R96 | 従業員適性ツールの見積/DPA/API条件はT839へ移管 |
| R75 | 営業メールAIの実メール接続後hardeningはT817_7 / T836へ移管 |
| R48 | 規約・プライバシーポリシー本文確定はT798 / PUBLIC-04へ移管 |
| R51 | 料金・特商法確定はT804 / PUBLIC-08へ移管 |
| R53 | Supabase Postgresアップグレード実行はT837へ移管 |
| R93 | Notion/Slack本送信用secret設定はT823 / T850へ移管 |

移管済みの課題は「なくなった」のではなく、開発完了判定の正しい場所へ移した。したがって `public_paid_launch` は引き続きNo-Goであり、T845、T849、T850、T852などの残ゲート完了後に再判定する。

## 古い/非採用サービス由来の課題

6/2社長プレゼン準備、Seedance/BytePlus、Canva/Figma自動化、Antigravity hooks/voice transcriptionなど、現行GA本番機能ではない課題はT848の外部SaaS/AIモデル凍結結果に合わせて `resolved` または `accepted_non_blocker` とした。

6/2向けの `docs/CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md` は、現行正本ではなく歴史的テンプレとして扱う。現行正本は `data/WBS.tsv`、`docs/WBS.md`、2026-06-17議事録、Go/No-Go資料である。

## PUBLIC-15判定

`PUBLIC-15` は `PASS` へ更新した。

ただし、これは「課題管理表・QA表に未分類open/未回答が残っていない」という意味であり、一般公開・有償ローンチの許可ではない。残るNo-Go要因は `PUBLIC-13`、`PUBLIC-14`、法務/価格/課金/負荷/実メール接続などの各ゲートで管理する。

## 公式ドキュメント確認メモ

今回の棚卸しでは、公式Docs確認対象をT848の凍結Runbookと同じ採用/非採用方針で見直した。特にGitHub Actions、Google Sheets API、Firebase Hosting、Supabase、Stripe、Slack、Notion、Figma、Canva、OpenAI Codex、Claude Codeの現在の扱いを確認し、secretや認証情報の実値を課題表、QA表、docs、NotebookLM、GitHub Issueへ残さない方針を維持した。
