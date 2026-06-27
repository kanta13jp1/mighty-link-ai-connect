# WBS 再レビュー 2026-06-26 第2セッション

作成日: 2026-06-26
担当レーン: VSCode + Codex
関連WBS: T844, T845, T846, T847, T848, T849, T850, T851, T852, T853, T854
関連Issue: #131, #132, #133, #134, #135, #136, #137, #138, #139, #140, #141

---

## 結論

T844からT852までで、企画、設計、実装、テスト、リリース、実運用、保守、会社運用引継ぎ、Firebase CI/CD本番デプロイ認証の主要ゲートはWBSに入っている。

ただし、T849の完了条件はGitHub Issues/Project未完了0を明記していた一方で、Sheets正本である `data/issues_tracker.tsv` と `data/qa_tracker.tsv` の最終棚卸しを独立ゲートとして明示していなかった。課題管理表やQA表に開発必須open/未回答が残ったままWBS全完了になると、サイト開発完了宣言の証跡が弱くなる。

そのため、次を追加した。

| ID | 内容 | 状態 |
| --- | --- | --- |
| T853 | 本レビュー。課題/QA最終ゼロゲートの追加判定 | 完了 |
| T854 | 課題管理表・QA表の未解決/未回答棚卸しと開発ブロッカーゼロ化 | 完了 |
| PUBLIC-15 | 課題管理表・QA表の開発必須open/未回答が0であることをpublic_paid_launchゲートへ追加 | PASS |
| R101 | 課題管理表・QA表の未解決/未回答が最終完了条件に明示されていないリスク | resolved |
| QA-78 | 課題管理表やQA表にopen/未回答が残っていてもWBS全完了時に完了と言えるかへの回答 | 回答済 |

## 2026-06-27 T854実施結果

`data/issues_tracker.tsv`、`data/qa_tracker.tsv`、GitHub Issues/Projectを棚卸しし、古いopen課題を解決済み、非ブロッカー、または後続WBS/Go-NoGoゲートへ移管した。QA表の英語 `answered` 表記は `回答済` へ正規化した。

`python scripts/audit_issue_qa_blockers.py --fail-on-blockers` の結果は `pass` であり、課題ブロッカー0件、QAブロッカー0件を `exports/issue_qa_blocker_audit.*` に証跡化した。詳細は [ISSUE_QA_BLOCKER_AUDIT_2026-06-27.md](ISSUE_QA_BLOCKER_AUDIT_2026-06-27.md) を正本とする。

## 補強後の完了定義

サイト開発完了の最終宣言は引き続きT849で行う。T849を完了できる条件は次の通り。

1. `data/WBS.tsv` の全タスクが完了している。
2. `data/release_go_no_go_criteria.tsv` の公開前必須ゲートが `PASS` または承認済みである。
3. GitHub Issues / Project #1 に未完了の開発必須Issueが残っていない。
4. `data/issues_tracker.tsv` の開発必須open課題が0、または非ブロッカー/保守移管として人間承認済みである。
5. `data/qa_tracker.tsv` の未回答/未承認QAが0、または非ブロッカー/保守移管として人間承認済みである。
6. Google Sheets、Google Calendar、Drive/NotebookLM向けdocsが最新のWBS/docsと同期済みである。
7. `main`、`master`、GA tag、GitHub Release、Firebase Hosting/Functions、公開デモURLの内容が一致している。
8. 会社アカウント移管、請求、権限、Break-glass、secret管理が会社運用へ引き継がれている。
9. GitHub ActionsからFirebase Hosting/Functionsへ、会社管理のWIF/service account/secret経路で本番deployできることが、アプリ変更を含むmain CIで確認されている。
10. secret、OAuth token、実メール本文、CSV原本、個人データ実値、契約金額実値がGitHub、Sheets、docs、NotebookLM、Issueへ記録されていない。

## 公式ドキュメント確認メモ

今回の判断では、次の公式ドキュメントを確認した。

- OpenAI Codex AGENTS.md
- Claude Code overview
- Gemini API models
- Google Sheets API batchUpdate
- Google Calendar API overview
- Firebase Hosting / Firebase CLI
- GitHub Actions / OIDC for Google Cloud / Projects automation / Releases
- Supabase Row Level Security

長い引用は残さず、WBSへ効く差分だけを反映した。追加の機能開発タスクではなく、完成判定の証跡を強くするための最終品質ゲートとしてT854を追加した。
