# Antigravity研修資料 視認性・デモ効率評価

## 対象

- `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`
- 16:9、全16枚、2026年8月8日評価

## 評価結果

| 評価軸 | 確認した証拠 | 判定 |
| --- | --- | --- |
| 物語 | 問い直す、探す、作る、直す、確認する、公開するの6段階を提示 | PASS |
| 時間 | 20分の標準進行と15分短縮版をスピーカーノートに用意 | PASS |
| 4概念 | Steering、Skills、MCP、Powerをデモ内の役割で説明 | PASS |
| `/grill-me` | 6質問、回答待ち、4区分要約、実行禁止を具体プロンプトで表示 | PASS |
| `/find-skills` | 公開元、利用実績、監査、コマンド、URLを比較する具体プロンプトを表示 | PASS |
| Build | HTML/CSSの初版と禁止事項、2 viewport確認を表示 | PASS |
| Steering | 変更、維持、検証、a11y、公式色を1枚に集約 | PASS |
| MCP | GitHub読取だけに限定し、未接続時は認証せず省略 | PASS |
| Publish | 専用repo、secret確認、正確な承認、公開後検証を表示 | PASS |
| 復旧性 | 90秒復旧、Skill結果予備、MCP省略、Pages予備を提示 | PASS |

## 検査証跡

- 全16枚を原寸PNGで個別確認: PASS
- `slides_test.py`: `Test passed. No overflow detected.`
- `check_template_fidelity.mjs`: `status=pass`, `issueCount=0`
- `python scripts/run_antigravity_live_demo.py`: H1-H10 PASS
- `python -m pytest tests/test_antigravity_live_demo.py -q`: 5件PASS
- Playwright: 1440x900 / 390x844で横溢れ0、文字溢れ0、console error 0

## 判定

投影資料は社長事前確認と社員研修に使用できる。Powerは公式の独立機能名ではなく研修上の呼称として説明し、SkillインストールとMCP認証は会場で行わない。公開は専用GitHub Pagesリポジトリだけで、Prompt 5の人による承認を省略しない。
