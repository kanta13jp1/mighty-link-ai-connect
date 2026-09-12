# public_paid_launch ゲート仕分けドラフト 2026-07-04（R112対応）

作成日: 2026-07-04
担当レーン: Claude Code
ステータス: **ドラフト（T833 2026-07-07 で関係者承認後に data/release_go_no_go_criteria.tsv へ反映）**
関連WBS: T863（本ドラフト） / T833 / T862 / T791
関連課題/QA: R112 / QA-92 / QA-93
関連docs: [INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md](INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md) / [PRODUCTION_GO_NO_GO_CHECKLIST.md](PRODUCTION_GO_NO_GO_CHECKLIST.md)

---

## 目的

2026-07-03 の T861 スコープ再定義（2026-07-08 は社内向けGA・実課金なし）により、有償公開前提で定義された public_paid_launch ゲートをそのまま 7/8 判定に適用すると実態と乖離する（R112）。本ドラフトは 21 ゲートを次の3分類へ仕分けし、T833（7/7）の承認材料とする。

- **維持**: 社内GA（7/8）の判定に引き続き必要
- **条件付きPASS**: 社内GAの範囲では満たしている。T862 有償化判断時に再確認
- **T862へ移管**: 有償公開時に再有効化。7/8 判定では対象外

## 仕分け表

| ゲート | 現状 | 提案 | 理由 |
| --- | --- | --- | --- |
| DEMO-01〜05 | PASS | 維持（PASS） | controlled demo スコープは変更なし |
| PUBLIC-01 セキュリティ監査 | PASS | 維持（PASS） | 社内利用でも本番システムとして必要 |
| PUBLIC-02 バックアップ/復元 | PASS | 維持（PASS） | 同上 |
| PUBLIC-03 SLA/KPI | PASS | 維持（PASS） | 同上 |
| PUBLIC-04 規約・ポリシー法務確認 | HUMAN_GATE | **維持**（T798、〜7/6） | 従業員個人データ（診断・勤怠・メール）を扱うため社内GAでも法務確認を維持。ただし課金規約・特商法の価格確定部分は T862 へ先送り可 |
| PUBLIC-05 同意チェックボックス | PASS | 維持（PASS） | 実装済み |
| PUBLIC-06 オンボーディング | BLOCKED | **維持**（T752、〜7/5） | 社内ユーザーの登録・アクティベーションに必要 |
| PUBLIC-07 法定ページ/フッター | PASS | 維持（PASS） | 実装済み |
| PUBLIC-08 価格CEO承認 | HUMAN_GATE | **条件付きPASS** | T804 は 2026-07-03 にプロジェクトオーナーが仮決定を承認して完了。社内GAでは実課金が発生しないため PASS 扱いとし、CEO の最終価格確認は T862 で実施 |
| PUBLIC-09 Stripe課金実装・Portal live | BLOCKED | **分割**: T791（Sandbox実装・Webhook検証）まで社内GAゲートとして維持。Customer Portal live 検証（T807）は **T862へ移管** | 実課金なしのため live 検証は不要。仕組みの実装検証（T791）は 7/5 まで |
| PUBLIC-10 負荷テスト/SLA | PASS | 維持（PASS） | T858 で達成済み |
| PUBLIC-11 営業メールAIマッチングMVP | BLOCKED | **維持**（T817/T817_7、〜7/5） | 社内ユーザーの中核機能 |
| PUBLIC-12 リリース/バージョニング | PASS | 維持（PASS） | 整備済み |
| PUBLIC-13 完成判定一式 | BLOCKED | **維持**（T845/T849/T850、〜7/8） | サイト開発完了判定はスコープ不変（有償化系タスクはゲート対象外: QA-91/QA-93） |
| PUBLIC-14 Firebase CI/CD認証 | BLOCKED | **維持**（T852、〜7/4） | デプロイ経路は社内GAでも必須 |
| PUBLIC-15 課題/QA ゼロ | PASS | 維持（PASS、T849で再確認） | 再確認時に R111（7/7解消予定）と R112（T833で解消）のクローズを確認する |
| PUBLIC-16 販売URL DNS/HTTPS | **PASS**（2026-07-04復旧） | 維持（PASS） | お名前.comドメイン情報認証の完了でclientHold解除。監視green（T855完了、暫定Go判断は不要に） |

**結果**: T862 へ移管するのは PUBLIC-09 の live 検証部分（T807）のみ。PUBLIC-08 は条件付き PASS。他はすべて社内GAゲートとして維持する。7/8 GA 判定に効く残ブロッカーは T752 / T791 / T798 / T817_7 / T845 / T849 / T850 / T852 / T855（+人間ゲート T819/T823/T831/T834/T836）で、昨日の再ベースライン日程と一致する。

## 公式ドキュメント確認メモ（2026-07-04）

- **Stripe は現在、レガシー test mode ではなく Sandboxes を推奨**（test mode は設定が live mode と共有される。Sandbox は最大5個、設定完全分離、V1/V2 API 対応）。T791 は default test mode ではなく**専用 Sandbox** で実装・検証し、live 設定への誤操作リスクを排除する。QA-93 の「test mode」は「Stripe Sandbox（または test 環境）」と読み替える。
- go-live 時（T862 後）は account switcher で Sandbox を抜け、live API key へ切替、secret は環境変数管理（コミット禁止）— 既存の T776 設計・secret 非記録ルールと整合。

## スケジュールのスリップ調整（2026-07-04）

- T811（PG14 バージョン確認・計画）: 7/3 必着が未完了のため 7/4 へ更新。T837（〜7/6）の前提として本日中の完了が必要。
- T819（7/2 定例の実施と報告）: 7/4 へ更新。実施済みであれば人間がステータスを完了にする。

## T833（7/7）への引き継ぎ

1. 本仕分け表を承認または修正する。
2. 承認後、`data/release_go_no_go_criteria.tsv` の PUBLIC-08（条件付きPASS化）と PUBLIC-09（T791スコープへの分割、T807 の T862 移管）を更新し、R112 を resolved にする。
3. PUBLIC-16 が未復旧の場合の暫定 Go 可否を判断する。
