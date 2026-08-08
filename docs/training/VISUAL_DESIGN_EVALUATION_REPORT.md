# Antigravity研修資料 視認性・デモ効率評価

## 対象

- `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`
- 16:9、全12枚、2026年8月8日評価

## 評価結果

| 評価軸 | 確認した証拠 | 判定 |
| --- | --- | --- |
| 物語 | 作る、改善する、公開するの3段階を2枚目で提示 | PASS |
| 時間 | 15分を4分、5分、4分、2分へ配分 | PASS |
| 観察箇所 | Manager、Editor / Terminal、Browser、GitHub Pagesの4箇所に限定 | PASS |
| Prompt 1 | HTML/CSSだけを作り、JavaScriptと公開を禁止 | PASS |
| Prompt 2 | Filter、Select、State、A11y、Design、Verifyを1枚に集約 | PASS |
| Prompt 3 | 公開先、承認文言、公開後検証を1枚に集約 | PASS |
| ブランド | MightyLINKの青`#00A5E3`と橙`#EF7E00`をアクセントに使用 | PASS |
| 画像 | 実際の完成版WebサイトとAntigravity UIを主役として配置 | PASS |
| 可読性 | 1280 x 720で長文を分割し、重要語を大きく表示 | PASS |
| 復旧性 | 90秒復旧と読み取り専用予備を別ページで提示 | PASS |

## 検査証跡

- 全12枚を原寸PNGで個別確認: PASS
- `slides_test.py`: `Test passed. No overflow detected.`
- `check_template_fidelity.mjs`: `status=pass`, `issueCount=0`
- `python scripts/run_antigravity_live_demo.py`: H1-H10 PASS
- `python -m pytest tests/test_antigravity_live_demo.py -q`: 4件PASS
- Playwright: 1440x900 / 390x844で横溢れ0、文字溢れ0、console error 0

## 判定

投影資料は社長事前確認と社員研修に使用できる。公開操作は専用GitHub Pagesリポジトリだけで行い、Prompt 3の人による承認を省略しない。
