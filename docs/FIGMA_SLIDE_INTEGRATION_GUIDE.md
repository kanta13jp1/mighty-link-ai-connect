# Figma Slide Template & Plugin Integration Guide

このドキュメントは、Figmaで作成した洗練されたデザイン（2026年モダンSaaS / Studio水準）を、PowerPoint（PPTX）および本プロジェクトの自動生成スクリプト（[`scripts/generate_ceo_presentation_deck.py`](../scripts/generate_ceo_presentation_deck.py)）と完全連携させるための実践ガイドです。

---

## 1. デザイントークン設計（Figma × Code同期）

プロジェクトルートの [`docs/design_tokens.json`](design_tokens.json) に、W3C Design Tokens Community Group規格に準拠したデザイントークンを定義しています。

### 主要カラーパレット（Figma Modern Studio）
| トークン名 | HEX / 値 | 用途 |
| :--- | :--- | :--- |
| `color.background.page` | `#0B0F19` (Deep Ink) | スライド全体の暗色キャンバス背景 |
| `color.background.surface` | `#151E2E` (Dark Slate) | 各種カード・パネルコンテナ背景 |
| `color.background.surfaceSubtle` | `#1E293B` | チップ・ヘッダー・ホバー領域 |
| `color.brand.cyan` | `#38BDF8` | プライマリアクセント、アイブロー、主要メトリクス |
| `color.brand.emerald` | `#10B981` | 成功・完了・検証済み指標 |
| `color.brand.amber` | `#F59E0B` | 進行中・注意喚起・同期中 |
| `color.brand.rose` | `#F43F5E` | ガードレール・リスク・重要項目 |
| `color.border.subtle` | `#2A364F` | カード境界線（1px） |

### タイポグラフィ・スペーシング
- **Display Font**: `Plus Jakarta Sans` / `Inter`（欧文タイトル・数字・アイブロー）
- **Body Font**: `Noto Sans JP` / `Yu Gothic`（本文・日本語解説）
- **Mono Font**: `JetBrains Mono` / `Consolas`（ID・ファイルパス・日時）
- **8px Grid**: 余白・パディングは `8px`, `16px`, `24px`, `32px` を厳格に適用
- **Corner Radius**: カードコンテナは `12px`、バッジ・チップは `9999px`（Pill形状）

---

## 2. Figmaスライドテンプレート構造（16:9 / 1920x1080）

Figmaで新規スライドを作成する際は、以下のフレーム構造でレイアウトを統一します。

```
Frame: Slide (1920 x 1080 px / 16:9)
├── Background (#0B0F19)
├── Layout Grid: 12 Columns (Margin: 80px, Gutter: 24px)
├── Header Component
│   ├── Decorative Top Bar (32x4px, #38BDF8)
│   ├── Eyebrow Tag (Mono 14px, Bold, #38BDF8, e.g. "01 / DECISION SCOPE")
│   └── Main Title (Display 36px, Bold, #F8FAFC)
├── Body Container (Auto Layout: Horizontal or 3-Column Grid)
│   ├── Card 1 (#151E2E, Radius: 16px, Border: 1px #2A364F)
│   ├── Card 2 (#151E2E, Radius: 16px, Border: 1px #2A364F)
│   └── Card 3 (#151E2E, Radius: 16px, Border: 1px #2A364F)
├── Evidence Panel (#151E2E, Radius: 12px, Bottom Docked)
└── Footer Component
    ├── Left: Slide Counter & Source Note (Mono 12px, #64748B)
    └── Right: Project / Deck Name (#94A3B8)
```

---

## 3. おすすめFigmaプラグイン & 連携手順

### 推奨プラグイン

1. **Tokens Studio for Figma (Figma Tokens)**
   - `docs/design_tokens.json` を直接インポートし、FigmaのColor Styles / Typography / Variablesを一括生成。
   - Figma上で色や角丸を変更後、JSONへ即時エクスポート可能。

2. **Pitchdeck Presentation Studio**
   - Figmaスライドをネイティブ編集可能な `.pptx` 形式で直接エクスポート。
   - テキストレイヤーが画像化されず、PowerPoint上でのテキスト編集が可能。

3. **Magicul Figma to PowerPoint Converter**
   - ベクター図形、アイコン、オートレイアウトをPPTXのネイティブシェイプに変換。

---

## 4. 自動生成スクリプトによるPPTX出力

本プロジェクトのスクリプトを実行することで、Figma Design Tokensに準拠したPPTXを即座に生成できます。

```powershell
# Figma Modern Studio テーマ (Dark Ink & カード型レイアウト)
python scripts/generate_ceo_presentation_deck.py --style figma-modern

# 従来のエグゼクティブライトテーマ
python scripts/generate_ceo_presentation_deck.py --style default
```

### 生成成果物
- PPTXファイル: `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02_figma-modern.pptx`
- サマリードキュメント: `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02_figma-modern.md`
- マニフェスト: `exports/knowledge_flow/mighty_skill_bridge_ceo_presentation_2026-06-02_figma-modern.json`
