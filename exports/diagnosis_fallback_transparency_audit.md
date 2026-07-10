# 診断フォールバック透明化 監査 (T885)

- 対象ファイル: index.html, src\index.html
- 総合判定: ✅ PASS (ドリフト0)

## 10仮説の検証結果

| 仮説 | 内容 | 判定 | 詳細 |
| :--- | :--- | :---: | :--- |
| H1 | index.html: runAnalysisが非OK時にサーバーdetailを読む | ✅ | OK |
| H2 | src/index.html: runAnalysisが非OK時にサーバーdetailを読む | ✅ | OK |
| H3 | 両ファイル: 404(静的デモ)と実バックエンドエラーを区別 | ✅ | 未区別=なし |
| H4 | 両ファイル: 実エラー時にスコアを『サンプル』と明示 | ✅ | 未明示=なし |
| H5 | 両ファイル: 静的デモ/オフラインの無言サンプルフォールバックを保持 | ✅ | 欠落=なし |
| H6 | 両ファイル: バナーヘルパー定義＋実行開始時クリアがある | ✅ | 欠落=なし |
| H7 | index.html と src/index.html の runAnalysis がバイト等価 | ✅ | 一致 |
| H8 | WBSにT885・UAT仕様書にTS-17(T885)が実在 | ✅ | WBS_T885=True, UAT_TS17=True |
| H9 | src/app.py: /api/matchが実在し429(expensive rate limit)/400(consent)を返しうる | ✅ | route=True, rate_limited=True, consent400=True |
| H10 | 診断フォールバック透明化が完全(ドリフト0) | ✅ | 先行ドリフト=なし |

> 実バックエンドが 429/500 等のエラーを返した時のみサンプル値である旨を明示し、
> 静的GitHub Pagesデモ(/api/match 404)・オフラインは従来の無言サンプル表示を維持する(デモ不変)。
