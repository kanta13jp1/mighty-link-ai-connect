# Google Antigravity 8/26ライブデモ運用手順

## 目的

2026年8月26日の社員向けAI研修で、Antigravityを使ったWeb開発を20分で実演する。`/grill-me`で要件を詰め、`/find-skills`で再利用可能な能力を探し、初版サイトを作り、Steeringで改善し、MCPで公開先を読み取り確認し、人の承認後だけGitHub Pagesへ公開する。

## 成果物

- 投影資料: `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`（全16枚）
- 概念説明: `docs/demo/antigravity_workshop/DEMO_CONCEPTS.md`
- Prompt 0: `docs/demo/antigravity_workshop/PROMPT_00_GRILL_ME.txt`
- Prompt 1: `docs/demo/antigravity_workshop/PROMPT_01_FIND_SKILLS.txt`
- Prompt 2: `docs/demo/antigravity_workshop/PROMPT_02_BUILD.txt`
- Prompt 3: `docs/demo/antigravity_workshop/PROMPT_03_STEER.txt`
- Prompt 4: `docs/demo/antigravity_workshop/PROMPT_04_MCP_CHECK.txt`
- Prompt 5: `docs/demo/antigravity_workshop/PROMPT_05_PUBLISH.txt`
- 要件: `docs/demo/antigravity_workshop/input/SITE_BRIEF.md`
- 完成版予備サイト: `docs/demo/antigravity_workshop/output/`
- 公開専用リポジトリ: `https://github.com/kanta13jp1/mighty-link-antigravity-live-demo`
- 公開URL: `https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/`

## 4概念

- **Steering**: 人がPlanやブラウザ結果などのArtifactへフィードバックし、次の実行方向を修正する操作。
- **Skills**: `SKILL.md`を中心に、専門手順、知識、資材をまとめた再利用可能なパッケージ。必要時だけ本文を読み込む。
- **MCP**: AIとローカルツール、データベース、外部APIを標準形式で接続する仕組み。本デモではGitHubの読み取りだけに使う。
- **Power**: 公式の独立機能名ではない。本研修ではSteering、Skills、MCP、Browser、権限を組み合わせ、検証可能な成果へ変える実行力を指す。

## 事前確認

1. Antigravityにログインし、Browserを起動できることを確認する。
2. `/grill-me`と`/find-skills`を利用できることを確認する。会場ではSkillをインストールしない。
3. 公開専用リポジトリだけを開き、`git remote -v`と`main`ブランチを確認する。
4. `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`があることを確認する。
5. GitHub MCPは任意とする。未接続なら認証を始めず、gitと公開URLの確認へ進む。
6. 次を実行し、H1-H10と回帰テストがすべてPASSであることを確認する。

```powershell
python scripts/run_antigravity_live_demo.py
python -m pytest tests/test_antigravity_live_demo.py -q
```

## 20分進行

| 時刻 | 操作 | 観客に見せる証拠 |
| --- | --- | --- |
| 00:00-03:00 | 4概念と`/grill-me` | 決定事項、除外、停止条件、成功条件 |
| 03:00-05:00 | `/find-skills` | 候補比較、公開元、利用実績、監査、推奨Skill |
| 05:00-09:00 | Build | HTML/CSSの初版サイト |
| 09:00-13:00 | Steering | 5カテゴリ、参加候補、a11y、ブランド変更 |
| 13:00-15:00 | MCP check | repo、branch、commit、Pages状態の読み取り |
| 15:00-19:00 | Publish | secret確認、合成データ確認、人の承認、push |
| 19:00-20:00 | Public proof | HTTPS、4セッション、件数、2件選択、commit一致 |

15分へ短縮する場合は、`/grill-me`を2分、`/find-skills`を1分、Buildを3分、Steeringを4分、MCPを1分、公開と確認を4分にする。学習目標と安全条件は省略しない。

## 公開承認

Prompt 5は`git add`、commit、pushの前に必ず停止し、`公開してもよいですか？`と確認する。登壇者が正確に`公開して`と返答した場合だけ公開操作へ進む。

公開前に確認する項目:

1. remoteとbranchが公開専用リポジトリの`main`である。
2. 顧客情報、社員情報、認証情報、トークンが含まれない。
3. `SYNTHETIC_DATA_ONLY`が残っている。
4. 本番`mightylink-app.com`のリポジトリやFirebase設定を変更していない。

## 成功条件

- DECISIONS: 対象、必須、除外、停止条件、成功条件が明文化される。
- FUNCTION: カテゴリ件数が`4,1,1,1,1`で、参加候補を2件選択できる。
- PUBLIC: GitHub PagesのHTTPS URLでタイトル、4セッション、機能、画像、最新commitを確認できる。

## 90秒復旧

- 90秒間進展がなければ、その段階のライブ操作を止める。
- 生成が止まったらローカル完成版を開く。
- `/find-skills`が遅ければ検証済み`anthropics/skills@frontend-design`を提示する。
- MCP未接続なら認証せず、gitと公開URLの確認へ進む。
- Pages待ちが長ければ準備済みURLとActions greenを示す。
- 会場でSkillインストール、MCP認証、本番リポジトリへの切替、承認前pushは行わない。

## 公式参照

- [Antigravity ArtifactsとSteering](https://antigravity.google/docs/artifacts)
- [Antigravity Agent Skills](https://antigravity.google/docs/skills)
- [Antigravity MCP](https://antigravity.google/docs/mcp)
- [Antigravity Permissions](https://antigravity.google/docs/permissions?app=antigravity)
- [GitHub Pagesの公開元設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
