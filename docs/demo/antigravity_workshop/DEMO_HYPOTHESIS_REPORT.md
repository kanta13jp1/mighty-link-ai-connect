# Antigravityスキル活用ライブデモ 10仮説検証レポート

実施日: 2026-08-08
対象: 6段階プロンプト、4概念説明、完成版予備サイト、GitHub Pages公開専用リポジトリ

## 検証結果

| 仮説 | 合否 | 合格条件 | 実測・証拠 |
| --- | --- | --- | --- |
| H1 6段階の物語が成立する | PASS | 要件整理、Skill探索、Build、Steering、MCP、Publishを別プロンプトにする | `PROMPT_00`から`PROMPT_05`を順序固定し、READMEに20分進行を記載 |
| H2 Build前に要件を詰められる | PASS | `/grill-me`が1問ずつ質問し、実行や変更を行わない | 6質問、回答待ち、4区分の要約、ファイル・コマンド・通信禁止を検証 |
| H3 Skillを品質比較できる | PASS | `/find-skills`が公開元、利用実績、監査、導入方法を比較する | 3検索語、3候補上限、インストール数、stars、監査、コマンド、URLを必須化 |
| H4 初版を小さく作れる | PASS | BuildはHTML/CSSとローカル画像だけを作る | JavaScript、commit、pushを禁止し、1440x900と390x844を確認 |
| H5 Steeringが変更契約になる | PASS | 変更、維持、検証が分離される | 5カテゴリ、2件選択、`aria-pressed`、`aria-live`、公式色、2 viewportを明記 |
| H6 Skillsを具体的に説明できる | PASS | `SKILL.md`と再利用性を説明し、デモSkillを示す | `/grill-me`、`/find-skills`、検証済み`anthropics/skills@frontend-design`を記載 |
| H7 MCPを読み取り専用にできる | PASS | GitHub MCPが任意で、書込と会場認証を行わない | repo、branch、commit、Pagesだけを読み取り、未接続時の1行フォールバックを固定 |
| H8 Powerを誤認させない | PASS | 公式機能名ではないと明記する | Steering、Skills、MCP、Browser、権限の組み合わせを研修上の呼称として定義 |
| H9 公開をfail-closedにできる | PASS | 専用repo、合成データ、secret確認、正確な承認を必須にする | remote/branch不一致、marker欠落、秘密情報、承認欠落で停止 |
| H10 回線障害と画面利用に耐える | PASS | 外部依存なし、a11y、2 viewport、90秒復旧を満たす | 外部参照0、見出し構造、5 filter、4 select、横溢れ0、読み取り専用予備3本 |

## ブラウザ実測

| 項目 | Desktop 1440x900 | Mobile 390x844 |
| --- | ---: | ---: |
| clientWidth / scrollWidth | 1440 / 1440 | 390 / 390 |
| scrollHeight | 1620 | 2549 |
| 文字溢れ | 0 | 0 |
| console error | 0 | 0 |
| 表示カード | 4 | 4 |

インタラクションはカテゴリ件数`4,1,1,1,1`、参加候補2件、選択名「AIで仕事を整理する / データを見える形にする」を確認した。

## PowerPoint実測

- 16枚を原寸PNGで個別確認: PASS
- `slides_test.py`: `Test passed. No overflow detected.`
- `check_template_fidelity.mjs`: `status=pass`, `issueCount=0`
- 具体プロンプト6本とスピーカーノートの出典を格納

## 証拠

- [デスクトップ](../../../exports/antigravity_demo_hypothesis_evidence/desktop_1440x900.png)
- [モバイル](../../../exports/antigravity_demo_hypothesis_evidence/mobile_390x844.png)
- [インタラクション](../../../exports/antigravity_demo_hypothesis_evidence/interaction_1440x900.png)
- [Playwright実測値](../../../exports/antigravity_demo_hypothesis_evidence/render_metrics.json)
- 自動検証: `python scripts/run_antigravity_live_demo.py`
- 回帰テスト: `python -m pytest tests/test_antigravity_live_demo.py -q`

## 残余リスク

会場回線、GitHub Actionsの待ち時間、Antigravity UI、skills.shの利用実績値は変動する。90秒で進展がなければ完成版と検証済みSkill結果へ切り替え、Skillインストール、MCP認証、本番リポジトリ操作は会場で行わない。
