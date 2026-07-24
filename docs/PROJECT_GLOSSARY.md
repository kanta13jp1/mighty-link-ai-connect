# 📚 Mighty Skill-Bridge プロジェクト用語集 (PROJECT GLOSSARY)

作成日: 2026-07-24 / 担当: コンプライアンス・法務・全体定義
関連ドキュメント: [`docs/JAPANESE_UI_UX_STYLE_GUIDE.md`](JAPANESE_UI_UX_STYLE_GUIDE.md) / [`docs/QUALITY_GUARD_CATALOG.md`](QUALITY_GUARD_CATALOG.md) / [`docs/INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md`](INTERNAL_LAUNCH_AND_BILLING_SCOPE_2026-07-03.md)

---

## 1. 概要

本ドキュメントは、**Mighty Skill-Bridge (MightyLINK AI Connect)** プロジェクト全体で使用されるプロダクト用語、機能名称、開発運用用語、およびコンプライアンス・課金用語の標準定義をまとめた単一正本用語集（Glossary）です。

プロジェクト関係者（PM、PdM、フロントエンド、バックエンド、AI、セキュリティ、SRE、QA、法務・課金）間での認識統一およびUI/UX文言の表記揺れ防止に適用します。

---

## 2. ドメイン・プロダクト別用語定義

### 2.1 プロダクト・ビジネス用語 (Product & Business Terms)

| 用語 | 英語表記 / 関連コード | 説明・定義 |
| :--- | :--- | :--- |
| **Mighty Skill-Bridge** | Mighty Skill-Bridge | **本プロダクトの正式名称**。AIを活用したエンジニア＆案件のフィットシミュレーターおよび社内HR統合プラットフォーム。 |
| **North Star KPI** | North Star KPI | プロダクトが創出する最重要成果指標。本プロジェクトでは**「営業マッチング成約時間の削減率」**を指標として定義。 |
| **料金プラン規格** | Pricing Plan Specification | 無料枠を含むプロダクトの価格設定。Free (¥0) / Standard (¥9,800/月) / Pro (¥29,800/月) / Enterprise (個別見積) の4構成。 |
| **仮名化ID** | Subject Pseudonym | 個人情報を自社DBに直接保持せず、オンボーディングや監査ログで識別するための暗号化/ハッシュ化ID（例: `onb-xxx`）。 |
| **ミキワメAI PoC** | Mikewame AI PoC | 社内適性・モチベーション診断の比較評価（RFI）において、最優先評価された外部連携・ベンダーPoC候補。 |

---

### 2.2 主要機能・AIパイプライン用語 (Feature & AI Terms)

| 用語 | 正則名称（推奨表現） | 非推奨・NG表記 | 説明・定義 |
| :--- | :--- | :--- | :--- |
| **営業メールAI** | **営業メールAIマッチング** | 案件マッチ, メールAI, Sales Email Match | POP3で取得した案件・人材メールをAI（Gemini等）で全件解析し、マッチング率と評価結果を自動算出・提示する機能。 |
| **適性・モチベーション** | **社内適性・モチベーション診断** | 心理テスト, 精神判定, メンタルチェック | 従業員の資質やモチベーション状態を6次元プロファイルで可視化する自己診断機能（※医療・心理診断や処遇決定には使用しない）。 |
| **勤怠・勤務表** | **勤務表・勤怠管理** | タイムカード, 作業報告, 出退勤アプリ | 勤怠打刻や勤務データから過重労働・稼働インデックスを自動解析する機能。 |
| **管理・運用** | **管理者統合ダッシュボード** | Admin UI, 管理画面, オペレーション画面 | 診断、勤怠、営業メールAIの解析結果やKPIを一元閲覧・操作する画面。 |
| **評価基準点** | Score Bands | - | 適性診断の判定基準。**面談目安**（0〜49.9点）、**注意**（50〜74.9点）、**正常**（75〜100点）の3段階で可視化。 |
| **生データ非保持原則** | Metadata Hub Principle | - | 従業員の詳細回答や外部ツールの生データは保持せず、同意状態と集計カテゴリ（評価メタデータ）のみを保持する安全設計。 |

---

### 2.3 開発・運用・品質管理用語 (Development, Ops & QA Terms)

| 用語 | 略称 / 関連コード | 説明・定義 |
| :--- | :--- | :--- |
| **社内GA** | Internal GA / Internal Launch | 一般公開前に、自社内の役職員を対象として実データ・無償で運用・検証を行う**「社内本番リリース」**フェーズ（2026-07-08〜）。 |
| **一般GA（有償公開）** | Public Paid Launch | 社外一般ユーザーへ公開し、StripeのLive課金を有効化する有償リリースフェーズ（T862 経営判断で決定）。 |
| **WBS** | Work Breakdown Structure | プロジェクトの全タスク、担当者、期限、進捗ステータスを追跡する単一正本台帳（[`data/WBS.tsv`](../data/WBS.tsv)）。 |
| **レーン・プリフライト** | Lane Preflight Guard | コミット/Push前に、24件の整合性ガードや全自動テストを一括実行して品質破壊を防ぐCI自動安全装置（`scripts/run_lane_preflight.py`）。 |
| **10仮説自動監査ガード** | 10-Hypotheses Guard | 各スクリプトや機能が正しく動作・整合しているかを、10個の厳格な検証仮説（H1〜H10）によって機械的に監査する仕組み。 |
| **Fail-closed** | Fail-closed | 認証情報の欠落やシステムエラーが発生した際、安全側に倒してアクセスを即座に自動遮断（503/401/403）するセキュリティ設計原則。 |

---

### 2.4 コンプライアンス・法務・課金用語 (Compliance, Legal & Billing Terms)

| 用語 | 略称 / 該当ファイル | 説明・定義 |
| :--- | :--- | :--- |
| **法定4文書** | 4 Statutory Docs | 利用規約（`TERMS_OF_SERVICE.md`）、プライバシーポリシー（`PRIVACY_POLICY.md`）、特商法表記（`TOKUSHOHO_NOTATION.md`）、課金規約・返金ポリシー（`BILLING_AND_REFUND_POLICY.md`）の総称。 |
| **【要法務確認】** | Legal Review Marker | 法定文書内で、社内確定または外部弁護士による法務判断を要する箇所を示す識別マーカー。 |
| **LEGAL_CONSENT_VERSION** | 法的同意バージョン定数 | ユーザーが同意した規約のバージョンを検証する識別定数（現行社内GA確定版: `MSB-LEGAL-2026-07-GA`）。 |
| **DPA** | Data Processing Addendum | 外部クラウド・SaaSツールとの間で締結する、個人データ処理や委託に関するデータ保護補足協定。 |
| **Stripe Billing Meters** | Stripe Meters API | 診断実行数やメールマッチング実行数に応じた従量課金を正確に計測・集計するStripe機能。 |
| **適格請求書（インボイス制度）** | Invoice System / Stripe Tax | 有償公開時に適用される、消費税額や適格請求書発行事業者番号を正しく表記・管理する課金機能（T813）。 |

---

## 3. 保守・整合ガードとの連携

- 本ドキュメントに記載されたドメイン正則用語（営業メールAIマッチング、社内適性・モチベーション診断、勤務表・勤怠管理、管理者統合ダッシュボード 等）は、[`docs/JAPANESE_UI_UX_STYLE_GUIDE.md`](JAPANESE_UI_UX_STYLE_GUIDE.md) および `scripts/audit_japanese_wording_consistency.py` と連携して継続的に自動検証されます。
