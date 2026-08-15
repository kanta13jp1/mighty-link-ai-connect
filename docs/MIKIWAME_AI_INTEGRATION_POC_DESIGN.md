# ミキワメAI 連携PoC アーキテクチャ＆UI仕様書（Proプラン差別化機能）

作成日: 2026-08-15  
作成責任者: 企画戦略担当 (Antigravity)  
対象プラン: **Pro プラン（月額 ¥29,800） / Enterprise プラン**  
関連WBS: `T839` / `T862` / `T909`
関連docs: [PRICING_PLAN_SPECIFICATION.md](PRICING_PLAN_SPECIFICATION.md) / [APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md](APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md) / [GROWTH_STRATEGY_ROADMAP.md](GROWTH_STRATEGY_ROADMAP.md)

---

## 1. 概要とビジネス価値

本機能は、「MightyLink AI Connect」のProプラン（月額 ¥29,800）およびEnterpriseプランにおける中核的差別化機能として、株式会社リーディングマークが提供する適性検査クラウド**「ミキワメ」の診断データ（CSV / JSONエクスポートデータ）をAIで解析・統合**し、以下の価値を提供します。

1. **カルチャー・現場適合度分析**: 案件の要求スキルに加え、エンジニアの性格傾向（外向性・協調性・ストレス耐性等）と現場環境の適合度を多面的にスコアリング。
2. **1-on-1フィードバック面談アドバイス**: 診断結果に基づく月次面談用パーソナライズドアイスブレイク＆支援質問を自動生成。
3. **高ARPU化の牽引**: Standardプラン（¥9,800）からProプラン（¥29,800）へのアップグレード動機を創出。

---

## 2. プライバシー保護・要配慮個人情報 厳格管理設計

[APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md](APTITUDE_MOTIVATION_DEMO_PRIVACY_DESIGN.md) のセキュリティ方針を完全準拠し、以下の「DB非保存・セッション限定」アーキテクチャを採用します。

```
[クライアント (ブラウザ)] 
   │ 
   │ 1. ミキワメ診断データ(匿名化ID+スコア)を投入
   ▼
[FastAPI /api/mikiwame-poc/analyze]
   │ 
   │ 2. メモリ内でのみ相性診断・面談ガイドをAI生成
   │    (PostgreSQL / Supabase へのDB書き込み・ファイル永続化は一切行わない)
   ▼
[レスポンス (JSON)] ➔ 画面上にセッション限定表示 (リロードで揮発)
```

- **非保存の担保**: サーバーログ・監査DBには個人名・診断生データは一切記録せず、実行件数カウンターのみをインクリメント。
- **利用目的の明示**: 人事考課・処遇決定には使用せず、社員の相互理解およびキャリア支援のための材料としてのみ利用することをUI上に明示。

---

## 3. データ入出力仕様

### 入力データフォーマット (JSON / CSV)
```json
{
  "engineer_alias": "Engineer-A (匿名ラベル)",
  "mikiwame_traits": {
    "stress_tolerance": 78,
    "cooperativeness": 85,
    "leadership": 62,
    "adaptability": 80,
    "logic_thinking": 75
  },
  "target_project_type": "SES常駐・アジャイル開発チーム"
}
```

### 出力レスポンス
```json
{
  "overall_culture_fit_score": 84,
  "fit_band": "良好・推奨 (Good Fit)",
  "team_compatibility_summary": "協調性と適応力が高く、チーム開発・コミュニケーション主体の現場において高い定着性が期待されます。",
  "recommended_interview_questions": [
    "「アジャイル開発において周囲と意見が分かれた際、どのように合意形成を進めたいですか？」",
    "「リモートと出社のハイブリッド環境において、モチベーションを維持するための工夫はありますか？」"
  ]
}
```

---

## 4. UI / 画面コンポーネント配置

統合ダッシュボード（`#aptitude-demo-section`）内のProプラン拡張タブとして**「ミキワメAI連携プレビュー」**を配置し、ワンクリックでサンプルデータの分析実演が可能なUIを提供します。
