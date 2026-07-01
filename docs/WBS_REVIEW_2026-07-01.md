# WBS 再レビュー 2026-07-01

作成日: 2026-07-01
担当レーン: VSCode + Codex
関連WBS: T752, T768, T770, T778, T780, T782, T791, T793, T798, T804, T807, T811, T813, T817, T817_7, T819, T823, T831, T833, T834, T836, T837, T839, T845, T849, T850, T852, T855, T857
関連Issue: #149

---

## 結論

2026-07-01時点で、企画、設計、実装、テスト、リリース、実運用、保守までの工程はWBSに存在している。サイト開発完了は引き続きT849で判定し、T849の完了条件として「全WBS完了、公開前Go/No-Goゲート、GitHub Issues/Project、課題管理表、QA表、Sheets/Calendar/Drive同期、main/master/GA tag/Release/Firebase整合、会社運用引継ぎ、secret非記録」を維持する。

今回新たに確認した不足は、Google Workspace OAuthが失効または未認証の場合、Sheets、Calendar、Drive/NotebookLM同期を完了扱いにできないことを、セッション開始/closeoutの実行ゲートとして明文化する点である。T825のRunbook自体は存在するが、2026-07-01現在の開発セッションでは、未認証時に「同期未完了のまま完了宣言しない」ことをWBS監査証跡へ残す必要がある。

そのため、T857を追加し、本レビューで完了した。

## 追加したタスク

| ID | 内容 | 状態 |
| --- | --- | --- |
| T857 | WBS現況再監査とGoogle Workspace OAuth同期再開ゲート確認 | 完了。Issue #149 / Project #1 Doneへ同期 |

## 未完了ゲートの分類

現時点の未完了WBSは、実装作業だけでなく、人間承認、会社アカウント移管、外部管理画面、DNS/ドメイン復旧、料金/法務判断を含む。すべてが完了するまでT849は完了にしない。

| 分類 | 主なWBS | 完了条件 |
| --- | --- | --- |
| 人間承認・会社判断 | T798, T804, T819, T823, T831, T833, T834, T839, T850 | 社長/会社側の承認、移管、問い合わせ、権限棚卸しが完了し、secretや契約実値を記録せず証跡化する |
| 本番運用・課金 | T791, T807, T813, T833 | Stripe Billing/Customer Portal/Tax、料金プラン、Go/No-Goが承認済みになる |
| 技術検証 | T752, T768, T770, T778, T780, T782, T811, T817_7, T837, T845, T852 | オンボーディング、多言語、負荷、SLA、DB、Gemini移行、営業メールhardening、Firebase CI/CDが検証済みになる |
| 外部接続・監視 | T836, T855 | 顧客メール環境OAuth承認、mightylink-app.com DNS/HTTPS監視復旧が完了する |
| 最終閉鎖 | T849 | すべての上流ゲートが完了し、GitHub/Sheets/Calendar/Drive/Firebase/Releaseが一致する |

## Google OAuth同期ゲート

Google Workspace同期は `authorized_user.json` を使うローカル認証が前提である。認証が未完了、失効、または取り消し済みの場合、次の状態として扱う。

- Sheets同期: 未完了
- Calendar同期: 未完了。完了済みWBSイベントの削除も未完了
- Drive/NotebookLM docs同期: 未完了
- T849: 完了不可

復旧手順は [GOOGLE_WORKSPACE_OAUTH_REAUTH_RUNBOOK.md](GOOGLE_WORKSPACE_OAUTH_REAUTH_RUNBOOK.md) を正本とし、会社アカウント `k-umezawa@ml-mightylink.com` で再認証する。`authorized_user.json`、`client_secret.json`、OAuth token、refresh tokenはGitHub、Sheets、docs、Issue、NotebookLM、Slack、チャットへ記録しない。

## スケジュール判断

T846、T847、T848、T854は前倒しで完了済み。一方で、2026-07-01時点ではT752、T770、T798、T811、T831、T834、T852、T855など、予定日を過ぎた未完了タスクが残っている。これらは多くが人間作業、外部管理画面、認証、DNS、会社移管に依存するため、WBS上は未完了のまま保持し、T849を前倒し完了にはしない。

後段タスクの前倒しは、上流ゲートが実際に完了したものだけに適用する。未完了タスクの予定日は、認証/会社移管/外部管理画面の状態確認後に再設定する。

## 公式ドキュメント確認メモ

今回の判断では、長い引用は残さず、WBSと同期運用に効く差分だけを確認した。

- Claude Code overview: https://code.claude.com/docs/en/overview
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex best practices: https://developers.openai.com/codex/learn/best-practices
- OpenAI Codex MCP: https://developers.openai.com/codex/mcp
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Google OAuth desktop/native apps: https://developers.google.com/identity/protocols/oauth2/native-app
- Google Sheets batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- Firebase Hosting GitHub integration: https://firebase.google.com/docs/hosting/github-integration
- Firebase Hosting custom domain: https://firebase.google.com/docs/hosting/custom-domain
- GitHub Actions OIDC: https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-google-cloud-platform
- GitHub Actions deployment hardening: https://docs.github.com/actions/deployment/security-hardening-your-deployments
- Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security

## 完了判定

T857は次をもって完了とする。

1. 未完了WBSを分類し、T849を完了不可にする残ゲートを明確化した。
2. Google Workspace OAuth未認証時のSheets/Calendar/Drive同期ブロックを明記した。
3. WBS全完了をサイト開発完了条件とする既存方針を維持した。
4. `data/WBS.tsv` と `docs/WBS.md` にT857を反映する。
