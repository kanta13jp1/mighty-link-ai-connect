# LP Design Taste Pack — 10 Patterns

作成日: 2026-05-24
オーナー: Claude Code レーン (UI design / docs)
対象 WBS: T658-extend (UI 方向性提示)
関連: [CEO_PRESENTATION_PREP](../CEO_PRESENTATION_PREP_2026-06-02.md) / [docs/wireframes/README.md](../wireframes/README.md)

---

## このパックの位置づけ

[UI Wireframes 10 patterns](../wireframes/README.md) は **「機能配置」** の判断材料。
本パックは **「デザインテイスト」** の判断材料。社長 6/2 で UI の方向性 (機能 + 見た目) を選ぶための独立した軸。

各 LP は Mighty Skill-Bridge (経歴 × 案件の AI フィット診断) をプロダクトテーマとし、
**異なる文化圏のランディングページ表現**を 10 種類提示する。Runway / Luma / Veo / Sora / Kling / Pika /
Higgsfield / ElevenLabs / Spline / Rive / Apple Vision Pro / Aesop / Oatly / Patagonia /
Stripe / Linear / Notion / Framer / Cowboy を参照した。

---

## 10 patterns matrix

| # | name | 参照 | キービジュアル | 想定顧客像 | キャッチコピー方向性 |
| --- | --- | --- | --- | --- | --- |
| **LP-01** | Cinematic Noir | Runway / Apple Vision Pro | full-bleed dark + 大型 serif + radial glow | 大手 / 上場、デザイン感度高 | 「AI が一瞬で見抜く適性」 |
| **LP-02** | Liquid Aurora | Luma Ray / Higgsfield | animated gradient blob + glass pill | 先端志向 SaaS バイヤー | 「採用判断を、光の速さで」 |
| **LP-03** | Research Whitepaper | DeepMind Veo / arXiv | 白基調 + citation + formula | エンタープライズ研究組織 | 「4-axis Fit Scoring」 |
| **LP-04** | Brutalist Mono | Sora / Linear (dark) | 黒白 + Plex Mono + scroll marquee | エンジニア決裁者 | 「Match. Score. Place.」 |
| **LP-05** | Pop Energy | Kling | 黄色 bg + magenta tag + emoji | スタートアップ / カジュアル HR | 「秒で見抜く」 |
| **LP-06** | Pastel Soft | Pika / Notion warm | パステル + 丸み + 柔らかい copy | 中小 HR / 応募者向け | 「やさしく、合う仕事と」 |
| **LP-07** | Glass Premium | Higgsfield / Apple VR | frosted glass + grain + subtle gradient | プレミアム SaaS / 経営層 | 「判断の解像度を、もう一段」 |
| **LP-08** | Warm Editorial | Aesop / Oatly / Patagonia | クリーム + condensed serif + 余白 | ブランド志向の HR コンサル | 「慎ましく、確かなフィット」 |
| **LP-09** | Precision Product | Stripe / Linear | 紺グラデ + grid + feature matrix + code | エンジニア / SaaS バイヤー | 「判断インフラを 1 つの API で」 |
| **LP-10** | Doc Modern | Notion / Framer | 白 + emoji + sidebar + 価格表 | チーム導入志向 / Self-serve | 「ドキュメントみたいに整理」 |

---

## 社長レビュー観点 (4 つ)

1. **キャラクター適合**: Mighty Skill-Bridge の「判断インフラ」性格に**最も合う**のはどれか
2. **顧客セグメント**: SES 営業 / 大手 HR / 経営層 / エンジニア決裁者のどこを最優先で取りに行くか
3. **ブランド色**: cyber palette (#0D0E15 + #00F0FF) を全面に出すか、editorial 系 (cream / serif) に振るか
4. **昇格対象**: 6/2 以降の本サイト (public demo URL) に昇格させるテイストを 1 つ選定

## ファイル

| 出力先 | 内容 |
| --- | --- |
| [`exports/landing-pages/index.html`](../../exports/landing-pages/index.html) | 10 LP カタログ (swatch グリッド + 社長レビュー観点) |
| [`exports/landing-pages/lp-01.html`](../../exports/landing-pages/lp-01.html) 〜 `lp-10.html` | 各 LP 単体ファイル (vanilla HTML/CSS, build なし, JS なし) |

## 公開 URL

- カタログ: <https://kanta13jp1.github.io/mighty-link-ai-connect/exports/landing-pages/index.html>
- 各 LP: 同 path 配下 `lp-01.html` 〜 `lp-10.html`
- 公開デモ (root) の上部 nav 「Sample LP」からも導線

## 制約遵守

- vanilla HTML/CSS single-file (新 build step / framework なし)
- JS は不要 (visual demo に専念、API call なし)
- root `index.html` の verify_public_demo.py 必須マーカーを保持
- `src/app.py` 不変 (Codex lane / 既存 `/exports` mount 流用)
