# Google Antigravity 8/26ライブデモ運用手順

## 目的

2026年8月26日の社員向けAI研修で、Antigravityを使ったWeb開発を30分で実演する。`/grill-me`で要件を詰め、`/find-skills`で再利用可能な能力を探して導入し、初版サイトを作り、`/frontend-design`で改善し、MCPで公開先を読み取り確認し、人の承認後だけGitHub Pagesへ公開する。残り30分は質疑応答と予備に使う。

## 成果物

- 投影資料: `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`（全30枚）
- 概念説明: `docs/demo/antigravity_workshop/DEMO_CONCEPTS.md`
- Prompt 0: `docs/demo/antigravity_workshop/PROMPT_00_GRILL_ME.txt`
- Prompt 1: `docs/demo/antigravity_workshop/PROMPT_01_FIND_SKILLS.txt`
- Prompt 2: `docs/demo/antigravity_workshop/PROMPT_02_INSTALL_SKILL.txt`
- Prompt 3: `docs/demo/antigravity_workshop/PROMPT_03_BUILD.txt`
- Prompt 4: `docs/demo/antigravity_workshop/PROMPT_04_APPLY_SKILL.txt`
- Prompt 5: `docs/demo/antigravity_workshop/PROMPT_05_MCP_CHECK.txt`
- Prompt 6: `docs/demo/antigravity_workshop/PROMPT_06_PUBLISH.txt`
- Q&A Prompt 7: `docs/demo/antigravity_workshop/PROMPT_07_OFFICIAL_VIDEO.txt`
- Q&A Prompt 8: `docs/demo/antigravity_workshop/PROMPT_08_NANO_BANANA.txt`
- Q&A Prompt 9: `docs/demo/antigravity_workshop/PROMPT_09_VISUAL_FEEDBACK_COMMENT.txt`
- 要件: `docs/demo/antigravity_workshop/input/SITE_BRIEF.md`
- 完成版予備サイト: `docs/demo/antigravity_workshop/output/`
- 公開専用リポジトリ: `https://github.com/kanta13jp1/mighty-link-antigravity-live-demo`
- 公開URL: `https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/`

## 4概念

- **Steering**: Kiroの正式機能名。Antigravityでは、Artifactへのinline feedbackやRulesによって実行方向を修正する。
- **Skills**: `SKILL.md`を中心に、専門手順、知識、資材をまとめた再利用可能なパッケージ。必要時だけ本文を読み込む。
- **MCP**: AIとローカルツール、データベース、外部APIを標準形式で接続する仕組み。本デモではGitHubの読み取りだけに使う。
- **Powers**: Kiroの正式機能名。Antigravityの機能名として扱わない。

## 実リハーサル結果

2026年8月9日に専用リポジトリで実施し、初回公開`05cfa7c`から最終改善`347ce89`まで11コミット、約78分を要した。公開URLはHTTPS 200で、デスクトップ1440x900とモバイル390x844はいずれも横スクロール0だった。

成功したこと:

- GitHub Pagesへの初回公開と継続的な改善。
- Google Antigravity公式YouTube動画`SVCBA-pBgt0`の埋め込み。
- 9製品、動画モーダル、Visual Feedback模擬体験、テーマ変更、検索、比較などの実装。
- `/frontend-design`によるタイポグラフィ、余白、暗色テーマの再設計。

本番へ持ち込まないこと:

- 5製品から9製品への拡張、料金・クォータ・診断・検索・エクスポートは30分本編の範囲外。
- CSSテーマ切替をNano Bananaと呼ばない。Nano Banana 2はAntigravityの画像生成Toolが使うモデルであり、Q&Aでは実画像を1枚生成する。
- 公開前に動画のtitle、author_name、author_urlを照合する。確認前に「公式」と表示しない。
- サイト内のVisual Feedbackシミュレーターと、AntigravityのScreenshot Artifactへの位置指定コメントを区別する。
- 比較サマリーが下部コンテンツを隠す問題を、Q&A Prompt 9の位置指定コメントで修正する。

この結果から、本編は7プロンプトへ固定し、Prompt 7-9はQ&Aまたは予備時間だけで使う。

## 事前確認

1. Antigravityにログインし、Browserを起動できることを確認する。
2. `/grill-me`と`/find-skills`を利用できることを確認する。`frontend-design`は本番中に専用repoへproject-localで導入する。
3. 公開専用リポジトリだけを開き、`git remote -v`と`main`ブランチを確認する。
4. `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`があることを確認する。
5. GitHub MCPは任意とする。未接続なら認証を始めず、gitと公開URLの確認へ進む。
6. ベースラインが5製品で、料金、クォータ、診断、検索、エクスポート、テーマ切替を含まないことを確認する。
7. 次を実行し、H1-H10と回帰テストがすべてPASSであることを確認する。

```powershell
python scripts/run_antigravity_live_demo.py
python -m pytest tests/test_antigravity_live_demo.py -q
```

## 30分本編

| 時刻 | 操作 | 観客に見せる証拠 |
| --- | --- | --- |
| 00:00-03:00 | 5製品とゴール | AIエージェントとの仕事の流れを固定 |
| 03:00-05:00 | `/grill-me` | 決定事項、除外、停止条件、成功条件 |
| 05:00-09:00 | `/find-skills` + install | 公開元、利用実績、監査、project-local導入 |
| 09:00-15:00 | Build | HTML/CSSの5製品初版 |
| 15:00-21:00 | `/frontend-design` | 絞り込み、最大2比較、a11y、2 viewport |
| 21:00-23:00 | MCP check | repo、branch、commit、Pages状態の読み取り |
| 23:00-30:00 | Publish + Public proof | 明示承認、push、HTTPS、5製品、件数、2件比較 |

Prompt 7-9は本編で実行しない。Q&Aで要望が出た場合だけ、公式動画、Nano Banana実画像、Screenshot Artifactへの位置指定コメントを順に使う。

## 公開承認

Prompt 6は`git add`、commit、pushの前に必ず停止し、`公開してもよいですか？`と確認する。登壇者が正確に`公開して`と返答した場合だけ公開操作へ進む。

公開前に確認する項目:

1. remoteとbranchが公開専用リポジトリの`main`である。
2. 顧客情報、社員情報、認証情報、トークンが含まれない。
3. `SYNTHETIC_DATA_ONLY`が残っている。
4. 本番`mightylink-app.com`のリポジトリやFirebase設定を変更していない。
5. 製品数が5件で、料金・クォータ・未承認の外部情報が追加されていない。

## 成功条件

- DECISIONS: 対象、必須、除外、停止条件、成功条件が明文化される。
- FUNCTION: 製品5件、フィルター件数`5,4,1,5`、最大2製品比較、2 viewportで横スクロール0。
- PUBLIC: GitHub PagesのHTTPS URLでタイトル、製品数、フィルター件数、2製品比較、最新commitを確認できる。

## 90秒復旧

- 90秒間進展がなければ、その段階のライブ操作を止める。
- 生成が止まったらローカル完成版を開く。
- `/find-skills`が遅ければ検証済み`anthropics/skills@frontend-design`を提示する。
- MCP未接続なら認証せず、gitと公開URLの確認へ進む。
- Pages待ちが長ければ準備済みURLとActions greenを示す。
- Prompt 7-9が90秒で進まなければ、実リハーサル済み公開URLとスクリーンショットを示す。
- 会場でglobal Skill install、MCP認証、本番リポジトリへの切替、承認前pushは行わない。

## リハーサル後・デモ後の復元

1. `frontend-design`の解決済みパスが`.agents/skills`直下であることを確認してから削除する。
2. `npx skills list --json`で`/grill-me`と`/find-skills`だけが残ることを確認する。
3. `git revert --no-commit <BASELINE>..<LAST_SHA>`で実演コミットを履歴付きで戻し、復元コミットをpushする。
4. 公開URLが準備ページへ戻り、`git status --short`が空であることを確認する。
5. `reset --hard`とforce pushは使わない。

## 公式参照

- [Antigravity ArtifactsとSteering](https://antigravity.google/docs/artifacts)
- [Antigravity Screenshot Artifacts](https://antigravity.google/docs/screenshots)
- [Antigravity Models / Nano Banana 2](https://antigravity.google/docs/models)
- [Antigravity Agent Skills](https://antigravity.google/docs/skills)
- [Antigravity MCP](https://antigravity.google/docs/mcp)
- [Antigravity Permissions](https://antigravity.google/docs/permissions?app=antigravity)
- [Google Antigravity公式紹介動画](https://www.youtube.com/watch?v=SVCBA-pBgt0)
- [GitHub Pagesの公開元設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
