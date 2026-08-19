# プロジェクト停滞タスク再監査（2026-08-19）

関連WBS: `T988` / `T791` / `T807` / `T813` / `T819` / `T823` / `T831` / `T834` / `T845` / `T849` / `T911` / `T944` / `T957` / `T958` / `T959` / `T977`

## 結論

コード量不足ではなく、実測証拠とWBS・経営資料の状態不一致が主な停滞要因だった。8月24日の有償化判断は、現時点では **NO-GO** とする。社内無償運用とSandbox準備は継続できるが、法務・SLA・実コスト・精度・人間サインオフが揃うまでStripe live切替と外部告知を行わない。

## 主要な発見

| 重要度 | 発見 | 実測 | 対応 |
| --- | --- | --- | --- |
| Critical | 8/24判断資料が未立証KPIを実績扱い | 最新取込成果物は702件、deterministic fallback。ラベル付き精度評価なし。月間SLAと実請求も未計測 | 判断資料と営業効果資料を訂正し、10仮説の証拠整合ガードを追加 |
| High | Stripe監査がSandbox隔離を実測せずPASS | `H9=True` 固定、テストファイル欠落、スクリプト未追跡 | live/不明keyをfail-closed、PII/value/identifier/Webhook検証を追加しテスト化 |
| High | 人間サインオフを自己記載だけで承認済みにしていた | インフラ提出パックに確認日・原本リンクが無い | 全項目を要人間確認へ戻し、T957を実行中へ変更 |
| High | WBSが実装済みタスクを未着手扱い | T845はT845_1/T921完了、T849は補助タスク3件完了 | T845/T849を実行中へ正規化し、残る人間工程を明記 |
| High | GMOメール削除インシデントが期限超過 | 削除元・パスワードローテーション・24時間保持証跡が未完了 | T944を8/20最優先へ再設定。完了までメール運用サインオフを禁止 |
| Medium | 課金系4タスクの日付が経営判断より前 | 8/24判定待ちなのに7月末期限のまま | Go後の依存順 `T791` → `T807/T813` → `T793` へ再配置 |
| Medium | Figma作業が外部利用枠待ちのまま期限超過 | T977はStarter利用枠依存 | 本番セキュリティと8/24判断を優先し、8/25以降へ移動 |
| Medium | 人手タスク4件が7月の期限切れ状態 | T819/T823/T831/T834が未着手のまま日付だけ反復延期 | 会議記録・Drive整理・認証情報失効・会社移管の完了条件を具体化し、8/20〜8/28へ依存順に再配置 |
| Medium | ローカル補助プロセスが多数残存 | 作業開始時点で既存のPython系補助プロセス66件（`http.server` 50件、Canva認証系14件、Figma Bridge 2件）を確認 | ユーザー作業中セッションの可能性があるため自動終了せず、PC負荷軽減時は所有者確認後に停止する |

## 2026-08-19に完了した作業

1. Stripe現行公式Docsを再確認し、Billing Meters/Meter EventsとCustomer Portalの現行手順が継続していることを確認。Metronome移行必須ではないため `R143` を解決した。
2. `scripts/verify_stripe_billing_meters_sandbox.py` をフェイルクローズ化し、既定モードがAPI未呼び出しのオフライン契約検証であることを明示した。
3. `tests/test_stripe_billing_meters_sandbox.py` を追加し、PII、正の整数値、一意identifier、複数v1署名、5分tolerance、live key遮断を固定した。
4. `scripts/audit_paid_launch_evidence.py` を29番目のプリフライトガードとして登録した。
5. 8/24判断資料、営業効果資料、インフラ提出パックを実測/未計測/人間確認待ちへ修正した。
6. GA E2Eレポートの日付固定値を廃止し、実行日のローカル日付を記録するよう修正した。
7. WBSを再ベースラインし、`T988` を完了した。
8. 期限超過のT819/T823/T831/T834を、証跡と依存関係を明記した実行可能な日程へ再配置した。
9. オフラインGemini評価が環境変数のAPIキーを継承していた問題と、T849の旧状態を固定したテストを修正し、full preflight 900件を `0 failed / 0 errors` で完了した。

## 残る実行順序

| 期限 | タスク | 完了条件 | 担当 |
| --- | --- | --- | --- |
| 8/20 | T944 | GMOアクセスログ、パスワード変更、接続元棚卸し、テストメール24時間保持 | 運用管理者 + Codex |
| 8/20 | T834 | WordPress/FTP一時資格情報を失効し、保存場所から削除して管理者ログインを確認 | 寛太梅澤 |
| 8/21 | T831 | 録画を会社Driveへ移動し、元所有者と移動先リンクを記録 | 寛太梅澤 |
| 8/23 | T845 | 最新E2E、T921証跡、ラベル付き精度評価の扱いを確認し、人間が最終UAT署名 | 経営・運用担当者 |
| 8/23 | T819 | 7/8会議の実施有無、決定事項、原本リンクを正式議事録へ確定 | 寛太梅澤 |
| 8/23 | T911 | 8/5会議の実施有無、決定事項、確認日を正本へ記録 | 寛太梅澤 |
| 8/23 | T957 | T944解決、インフラ責任者の確認日・原本リンク、最新full preflight | インフラ責任者 + PM |
| 8/24 | 有償化判断 | `audit_paid_launch_evidence.py` PASS後にGo/No-Go/保留を署名 | CEO |
| 8/25以降 | T791/T807/T813/T793 | Goの場合のみ依存順にSandboxからliveへ進める | Codex + 人間 |
| 8/25〜8/28 | T823 | T831とGo判定後、会社所有権・請求・secretsを移管し公開系を再検証 | 寛太梅澤 + Codex |

## 現行公式根拠

- [Stripe Usage-based billing](https://docs.stripe.com/billing/subscriptions/usage-based)
- [Stripe pay-as-you-go implementation](https://docs.stripe.com/billing/subscriptions/usage-based/implementation-guide)
- [Stripe Customer Portal](https://docs.stripe.com/customer-management/integrate-customer-portal)
- [Stripe webhook verification](https://docs.stripe.com/webhooks)

## 判定境界

- `audit_legal_disclosures.py` のPASSは必須項目と文書間整合の判定であり、未確定31件や弁護士承認の完了を意味しない。
- `audit_pricing_consistency.py` のPASSは価格ドリフト0の判定であり、未確定マーカー3件の解消やCEO承認を意味しない。
- 単発のHTTP監視7/7 PASSは月間稼働率99.9%の実績ではない。
- 702件の取込成果物は1日1,000件の継続負荷試験でも、精度80%の評価でもない。
