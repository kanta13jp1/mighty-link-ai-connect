# 従業員適性・状態把握ツール ショートリストPoC計画

- 対象WBS: T838
- 関連課題: R31, R32, R36, R96
- 作成日: 2026-06-22
- レーン: VSCode + Codex / VSCode + Claude Code
- 技術前提: バックエンド Firebase、DB Supabase、レジストラ お名前.com
- 前提正本: [EMPLOYEE_ASSESSMENT_TOOL_RESEARCH.md](EMPLOYEE_ASSESSMENT_TOOL_RESEARCH.md)

## 結論

T838では、MightyLink本体が従業員の精神状態や健康状態をAIで診断する方針は採らない。PoC対象は、外部の適性検査、パルスサーベイ、組織改善サーベイを使い、MightyLink側は同意、実施メタデータ、集計カテゴリ、レビュー記録だけを扱う「評価メタデータ連携」に限定する。

一次ショートリストは次の3サービスとする。

| 優先 | サービス | 主目的 | PoCで確認する理由 | MightyLink保存範囲 |
| --- | --- | --- | --- | --- |
| 1 | ラフールサーベイ | 組織改善、離職防止、エンゲージメント/コンディション把握 | 従業員状態の把握と組織改善に寄せやすく、T832の禁止線に合う | 実施ID、同意版、回答完了、部署などの非識別集計カテゴリ、レビュー記録 |
| 2 | HRBrain パルスサーベイ wellday | 従業員コンディションの継続把握 | パルスサーベイと人事データ管理の連携余地を比較できる | 実施ID、同意版、回答完了、非識別サマリ、レビュー記録 |
| 3 | ミキワメAI 適性検査 | 採用・配置・オンボーディング補助 | 採用基準の可視化、面接ガイド、候補者負担の軽い検査を比較できる | 受検完了、評価カテゴリ、面接確認ポイント、レビュー記録 |

補欠候補は、法定ストレスチェック寄りにする場合はWevox Stress Check、既にSmartHR契約がある場合はSmartHR従業員サーベイ、標準化された採用検査を優先する場合はSPI3とする。

## PoC禁止線

- 医療診断、精神疾患の推定、治療方針提示は行わない。
- 採用、配属、評価、契約継続を外部サービスのスコアだけで自動決定しない。
- ストレスチェックや心理・健康系データの生回答をSupabaseへ保存しない。
- 個人単位の心理・健康スコアをR36の外部法務レビュー前にMightyLinkへ取り込まない。
- 氏名、メール、社員番号、病歴、健康診断結果などの直接識別情報をAIモデルやNotebookLMへ送らない。

## 連携方式の暫定設計

PoCの最初の連携はCSVまたは管理画面からの手動エクスポートを優先する。API連携、Webhook、SSO、社員マスタ同期は、契約条件とDPA確認後の拡張扱いにする。

Supabaseに保存してよい最小項目は次の範囲に限定する。

| 項目 | 保存可否 | 補足 |
| --- | --- | --- |
| vendor_id / service_name | 可 | 外部サービス名とPoC識別子のみ |
| subject_pseudonym | 可 | 社内の直接識別子とは別のPoC用ID |
| consent_version / consented_at | 可 | 本人説明と撤回手順を追跡 |
| completed_at / import_batch_id | 可 | 受検・回答完了の事実 |
| aggregate_bucket / recommendation_category | 条件付き可 | 個人の健康・心理状態を直接示さない粗いカテゴリに限定 |
| raw_answers / health_score / stress_score | 不可 | 外部サービスまたは制度運用内に閉じる |
| reviewer_id / review_decision / next_action | 可 | 人間レビューと説明責任の証跡 |
| deletion_due_at / deleted_at | 可 | 削除SLAと撤回対応の証跡 |

## ベンダー確認チェックリスト

公開ページでは確定しきれないため、T839で次をベンダーへ確認する。

| 項目 | 確認内容 | 判定基準 |
| --- | --- | --- |
| 契約 | 最低契約期間、初期費用、月額、従量課金、トライアル可否 | PoCだけで過剰な固定費を負わない |
| DPA/NDA | 個人情報処理、再委託、国外移転、監査権、秘密保持 | R36/T798の法務確認に渡せる |
| 個人情報 | 取得項目、要配慮情報該当性、本人同意、本人開示、利用停止 | 利用目的を限定できる |
| 権限管理 | 管理者、人事、マネージャー、本人、産業医の閲覧範囲 | 不利益取扱い防止の権限分離ができる |
| 連携 | CSV、API、Webhook、Google Workspace、SSO、監査ログ | 初回はCSV、将来はAPIに移行できる |
| 削除SLA | 退職者、同意撤回、PoC終了時の削除期限と証跡 | 3営業日から2週間以内の運用に合わせられる |
| 説明責任 | スコア根拠、面接ガイド、本人向け説明、管理者教育 | 自動判断ではなく人間レビューに使える |
| サポート | 導入支援、管理者トレーニング、問い合わせ窓口 | 小規模PoCでも運用できる |

## PoC評価基準

| 評価軸 | 合格ライン |
| --- | --- |
| 法務適合 | R36/T798の外部法務レビューに必要なDPA、同意、削除、権限情報が揃う |
| データ最小化 | MightyLinkへ生回答、直接識別子、健康・心理スコアを保存せずに運用できる |
| 運用負荷 | 人事担当がCSV出力、同意管理、レビュー記録を月次で回せる |
| 説明可能性 | スコアや推奨が、面接・1on1・育成計画の補助材料として説明できる |
| 公平性 | 採用・配属・評価で単独自動判断を避け、本人説明と不服申立て導線を設けられる |
| 連携拡張性 | PoC後にAPI/SSO/監査ログ連携を検討できる |
| 費用 | 見積がCEO承認前の小規模PoC予算に収まる |

## R32の実装範囲再定義

R32の「AI適性状況診断ツール」は、当面は診断AIではなく、外部サービス結果の同意・取込・人間レビューを管理する評価メタデータHubとして再定義する。

実装候補は次の順で進める。

1. 外部サービス名、PoC実施ID、同意版、回答/受検完了、レビュー結果を登録する管理画面。
2. CSVインポート時の列マッピング、匿名ID化、secret/PII混入検査。
3. 採用・配置・育成・組織改善の用途別に、閲覧権限とレビューコメントを分ける。
4. R36/T798完了後に限り、個人単位カテゴリの保存可否を再判定する。
5. public_paid_launchのGo/No-Goでは、心理・健康データを扱う機能はHUMAN_GATEのまま別判定にする。

## 日程

| 日付 | 内容 | WBS |
| --- | --- | --- |
| 2026-06-22 | ショートリスト、禁止線、PoC評価基準を確定 | T838 |
| 2026-06-23 - 2026-06-26 | ベンダー問い合わせ、見積、DPA、API/CSV、削除SLA確認 | T839 |
| 2026-06-27 - 2026-06-30 | R36/T798の外部法務レビューへ論点を渡し、PoC実施可否を判定 | T798 / R36 |

## 公式情報確認メモ

2026-06-22時点で次を確認した。

- 厚生労働省: 小規模事業場ストレスチェック制度実施マニュアル https://www.mhlw.go.jp/stf/newpage_69680.html
- 厚生労働省: 厚生労働省版ストレスチェック実施プログラム https://stresscheck.mhlw.go.jp/
- 個人情報保護委員会: 雇用管理分野における健康情報の取扱い https://www.ppc.go.jp/personalinfo/legal/ryuuijikou_health_condition_info/
- SPI3: https://www.spi.recruit.co.jp/
- ミキワメAI 適性検査: https://mikiwame.com/aptitude-test.html
- ラフールサーベイ: https://survey.lafool.jp/
- HRBrain パルスサーベイ wellday: https://www.hrbrain.jp/pulse-survey
- Wevox Stress Check: https://get.wevox.io/service/stresscheck
- SmartHR 従業員サーベイ: https://smarthr.jp/talent-management/function/survey/
- Google Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- Firebase Hosting: https://firebase.google.com/docs/hosting
- Supabase Docs: https://supabase.com/docs/guides/getting-started
- GitHub Issues / Projects / Actions: https://docs.github.com/en/issues
- OpenAI Codex docs / Codex manual, Anthropic Claude Code docs, Google Gemini docs, Microsoft Foundry docs, Meta Llama docs, Amazon Bedrock docs, Apple ML/HIG, xAI, Kimi, MiMo, DeepSeek, ByteDance Seedance, Slack, Notion, Obsidian, Unity, Figma, Canva, Reddit, InsForge, Firecrawl, Discord, Stripe, お名前.com 公式ページ。
