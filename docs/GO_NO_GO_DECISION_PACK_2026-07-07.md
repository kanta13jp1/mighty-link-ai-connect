# 社内GA Go/No-Go 判定パック（T833・2026-07-07）

作成日: 2026-07-04
担当レーン: VSCode + Claude Code
用途: 2026-07-07 の T833（Go/No-Go 再判定）当日の判定材料一式。判定結果は本docsの末尾に記入し、`data/release_go_no_go_criteria.tsv` と R112 を更新する。
関連WBS: T867（本パック） / T833 / T849 / T863
関連docs: [GO_NO_GO_GATE_TRIAGE_2026-07-04.md](GO_NO_GO_GATE_TRIAGE_2026-07-04.md) / [INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md](INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md) / [CEO_MEETING_AGENDA_2026-07-08.md](CEO_MEETING_AGENDA_2026-07-08.md)

---

## 1. 判定の前提（決定済み事項）

- 2026-07-08 のリリースは**社内向けGA**（実課金なし。T861）。
- ゲート仕分けは T863 ドラフトのとおり: T862（有償化）へ移管するのは PUBLIC-09 の live 検証部分のみ、PUBLIC-08 は T804 仮承認で条件付き PASS、他は維持。**T833 でこの仕分けを正式承認する。**

## 2. ゲート現況（2026-07-04 時点）

**PASS 済み: 14 ゲート**（DEMO-01〜05、PUBLIC-01/02/03/05/07/10/12/15/16）。PUBLIC-16（販売URL）は 7/4 に clientHold 解除で復旧済み。

**残 7 ゲートと PASS 条件:**

| ゲート | 現況 | PASS にする条件 | 担当 | 期限 |
| --- | --- | --- | --- | --- |
| PUBLIC-04 法務確認 | HUMAN_GATE | T798: 利用規約・プライバシーポリシーの確認完了（課金条項は T862 先送り可） | 人間 + Claude | 7/6 |
| PUBLIC-06 オンボーディング | BLOCKED | T752: 実装完了と動作確認 | Antigravity | 7/5 |
| PUBLIC-08 価格承認 | HUMAN_GATE | T833 で条件付き PASS を承認（T804 は 7/3 完了済み） | 判定会 | 7/7 |
| PUBLIC-09 Stripe課金 | BLOCKED | T791: Sandbox 実装・Webhook 検証完了。live 部分は T862 移管を承認 | Codex + 判定会 | 7/5 |
| PUBLIC-11 営業メールAI | BLOCKED | T817_7: hardening 完了（実メール接続は下記 §4） | Codex + Claude Code | 7/5 |
| PUBLIC-13 完成判定一式 | BLOCKED | T845 UAT green（**本番DB実書き込み確認を含む**・R114 反映）、T850 引継ぎ | 全レーン | 7/7 |
| PUBLIC-14 CI/CD認証 | BLOCKED | T852: WIF/ADC 再構成と main deploy green | Codex + 人間 | 7/4 |

## 3. 人間依存ゲートの残り（R111）

T798（法務・7/6）/ T823（会社移管・7/5）/ T831（録画整理・7/4）/ T834（旧サイト認証情報削除・7/4）/ T836（メール接続・7/4→§4）。T819（定例）は 7/8 15:00 に確定済み。未達分は 7/7 判定で扱いを決める。

## 4. 営業メール実接続の扱い（R113・判定上の推奨）

接続情報は CEO へ依頼済み・未受領（7/8 定例で受領見込み）。判定日 7/7 時点で未受領の場合は、**案A（検証済み PoC データで 7/8 に GA、実接続は受領後に追加検証）を前提として Go と判定し、7/8 15:00 の CEO 定例で最終確認する**ことを推奨する。案B（GA 延期）を選ぶ場合は 7/9-7/10 へ全体を 1-2 日スライドする。

## 5. インフラ前提の確認事項

- **Supabase Postgres**: 本番は **PostgreSQL 17.6** と確認済み（2026-07-04 T811完了）。PG14 EOL の影響はなく、**T837 のアップグレード実行は不要と判定して完了**（[SUPABASE_INFRA_AUDIT_2026-07-04.md](SUPABASE_INFRA_AUDIT_2026-07-04.md)）。
- **バックアップ（PUBLIC-02 再評価要）**: Supabase Daily Backup CI が 6/22 以降一度も成功していないことが判明（R116）。暫定ローカルバックアップは 7/4 取得済み。恒久修復は T870（WIF再構成・バケット作成・secret登録、T852と同時）。**7/7 判定で PUBLIC-02 の扱い（暫定バックアップでの条件付きPASS可否）を決める**。
- **追加スキーマ欠損（R117）**: **解消済み（2026-07-05）**。migration 3件を適用し本番は22テーブルに。フィードバック・サポートの本番保存を合成データで検証済み（T871完了）。営業メール系9テーブルのパイプライン経由検証は T817_7/T845 で実施する。
- **本番スキーマ**: R114（テーブル欠損）は 7/4 復旧済み。再発防止 T866（Codex・7/5）は GA 前完了が望ましいが、判定ブロッカーにはしない（スキーマは適用済みのため）。
- **DNS/HTTPS**: 販売URL 復旧済み・監視 green。T823 会社移管時の WHOIS 変更で再認証が発生する点のみ注意。

## 6. 判定当日（7/7）のチェックリスト

```powershell
python scripts/check_uptime_targets.py
python scripts/diagnose_custom_domain_dns.py
python scripts/audit_issue_qa_blockers.py --fail-on-blockers
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
python scripts/check_supabase_postgres_version.py
```

1. 上記スクリプトが green であることを確認する。
2. §2 の残 7 ゲートの完了状況を確認し、`data/release_go_no_go_criteria.tsv` の current_state を更新する。
3. T863 仕分け（PUBLIC-08 条件付き PASS / PUBLIC-09 分割）を承認し、R112 を resolved にする。
4. §4 の案A/案B を仮決定する（7/8 定例で最終確認）。
5. 判定結果を下表に記入し、Sheets・Issue・Project を更新する。

## 7. 判定結果（7/7 に記入）

| 項目 | 結果 | 備考 |
| --- | --- | --- |
| 社内GA（7/8）可否 | | |
| ゲート仕分け承認（R112） | | |
| 営業メール 案A/案B | | |
| 未達ゲートの扱い | | |
| 判定参加者 | | |
