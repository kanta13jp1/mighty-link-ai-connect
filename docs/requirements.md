# 📄 Mighty Skill-Bridge: 要件定義書 (requirements.md)

> **Mighty-Link AI Connect: Project "Mighty Skill-Bridge"**
> *人と人、ビジネスとビジネス、テクノロジーを力強く繋ぎ、エンジニアの未来と最適な案件を架橋するAIフィットシミュレーター*

---

## 1. プロダクト概要

### 1.1 背景と目的
エンジニアのスキルシート（経歴書）と案件定義書（アサイン要件）のマッチングは、従来のキーワード一致や手動査定では、「本質的な志向性の不一致」「潜在的スキルの見落とし」「ソフトスキルのミスマッチ」といった課題を抱えていました。
**『Mighty Skill-Bridge』** は、Google Gemini APIで公式提供中の現行モデルとマルチモーダル解析技術を活用し、履歴書/経歴書（PDFや画像）と案件定義書（テキストやPDF）を高度にパースし、単なるキーワードマッチを超えた「多次元フィット分析」を瞬時に実行する、次世代のエンジニア＆案件 AIフィットシミュレーターです。

### 1.2 コアバリュー
- **テクノロジーの架け橋**: 最先端のAIモデルが、エンジニアの経歴に隠された「潜在能力」や「得意領域」を最大化して評価。
- **直感的ビジュアル**: 社長プレゼンではSeedance風の黒基調AI studio UIを採用し、Mighty Blue / Green / Yellow / Roseのアクセントで4軸分析を映像生成プロダクトのように見せる。
- **Google Workspace API (Sheets/Docs/Calendar) 連携**: 案件マッチング結果やWBSステータスが、Google Sheets / Docs / Calendar と自律的に連携。

---

## 2. 機能要件 (Core Features)

### 2.1 【フロントエンド】マルチモーダル・ドラッグ＆ドロップ UI
- エンジニアのスキルシート（PDF/Word/画像等）をドロップするエリア。
- 案件の募集要項（PDF/テキスト等）をドロップ、またはテキスト入力するエリア。
- アップロード中のローディングアニメーション（滑らかなマイクロインタラクション）。

### 2.2 【AIコア】多次元フィット・エンジン (Gemini API / deterministic fallback)
- **スキル・フィット (Skill Fit)**: 使用技術、フレームワーク、アーキテクチャ設計力のマッチ度。
- **カルチャー・フィット (Culture Fit)**: 過去の在籍企業形態、アジャイル/ウォーターフォール等の開発文化マッチ度。
- **グロース・フィット (Growth Fit)**: エンジニアが今後目指したいキャリア像と案件の親和性。
- **パフォーミング・フィット (Performing Fit)**: 即戦力として稼働した場合の想定生産性・キャッチアップ速度。

### 2.3 【ビジュアライズ】フィット分析レポート
- **多角レーダーチャート**: スキル、カルチャー、グロース、パフォーミングの4軸を可視化。
- **フィット要約 & フィードバック**: なぜこの案件とマッチするのか、どの部分が不足しているかをAIが丁寧かつ論理的に説明。
- **面談想定質問ジェネレーター**: 案件参画に向けて、面談時に想定される深掘り質問と、その模範解答・アピールポイントをAIが自動生成。

---

## 3. 非機能要件 & 技術スタック

- **Core Logic**: HTML5 + Vanilla JavaScript (ES6+)
- **Styling**: Vanilla CSS (CSS Variables を用いたテーマ設計、モダンなダーク＆ライトハイブリッドモード、ガラスモフィズム)
- **Analytics/Charts**: Chart.js (CDN経由で超軽量ロード)
- **Backend API**: Gemini API 現行モデル連携 (Mock & Live モード両対応)
- **Collaboration**: Google Sheets API & Google Docs API 自律同期

---

## 4. Sheets Live & Docs Live 連携仕様 (Google Workspace API)

- **同期アクション1 (WBS進捗)**: 各タスク完了時に `sync_wbs_to_sheets.py` が WBS シートを自動更新。
- **同期アクション2 (マッチングデータベース)**: ユーザーがシミュレーターでマッチングを実行するたびに、結果（エンジニア名、案件名、マッチング率、レーダーチャート用スコア、面談想定質問）が Google Sheets の「マッチングログ」シートへ自動蓄積。
- **同期アクション3 (面談ロードマップ同期)**: 最もフィット率が高かった案件に対するエンジニア用の「1ヶ月キャッチアップ計画」を Google Docs Live 用に自動文書化し、共有可能なURLを即時発行。

---

## 5. UI/UX デザインシステム (AI Studio System)

- **メインカラー (Primary)**: `#8BDCFF` (Mighty Blue - AI解析 / 透明感)
- **セカンダリカラー (Secondary)**: `#BAFF66` (Mighty Green - 成長とマッチ成立)
- **アクセントカラー**: `#FFD166` / `#FF6CAB` (判断材料と注意点を分ける)
- **背景 (Background)**: `#030303` / `#090A0C` (Seedance風の黒基調AI studio)
- **フォント**: Google Fonts 'Outfit' & 'Noto Sans JP'
- **スタイルエフェクト**: 8px角のパネル、細いグリッド、映像プレビュー風の分析フレーム。

---
*Created and approved as part of WBS Task T101.*
