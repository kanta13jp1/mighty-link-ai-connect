# Google Antigravity 8/26ライブデモ運用手順

## 目的

2026年8月26日の社員向けAI研修で、AntigravityによるWeb開発を15分で実演する。デモは「新規作成」「機能・デザイン改善」「GitHub Pages公開」の3段階とし、各段階の差分をブラウザで確認する。

## 成果物

- 投影資料: `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`（全12枚）
- Prompt 1: `docs/demo/antigravity_workshop/MAIN_PROMPT.txt`
- Prompt 2: `docs/demo/antigravity_workshop/PROMPT_02_IMPROVE.txt`
- Prompt 3: `docs/demo/antigravity_workshop/PROMPT_03_PUBLISH.txt`
- 要件: `docs/demo/antigravity_workshop/input/SITE_BRIEF.md`
- 完成版予備サイト: `docs/demo/antigravity_workshop/output/`
- 公開専用リポジトリ: `https://github.com/kanta13jp1/mighty-link-antigravity-live-demo`
- 公開URL: `https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/`

## 事前確認

1. Antigravityにログインし、Browserを起動できることを確認する。
2. 公開専用リポジトリをローカルへcloneし、Antigravityでそのフォルダだけを開く。
3. `git remote -v`が公開専用リポジトリを指し、ブランチが`main`であることを確認する。
4. `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`があることを確認する。
5. 次の検証を実行し、H1-H10がすべてPASSであることを確認する。

```powershell
python scripts/run_antigravity_live_demo.py
python -m pytest tests/test_antigravity_live_demo.py -q
```

## 15分進行

| 時刻 | 操作 | 観客に見せる変化 |
| --- | --- | --- |
| 00:00-04:00 | Prompt 1を実行 | 要件から4つの研修カードを持つWebサイトを新規作成 |
| 04:00-09:00 | Prompt 2を実行 | 5カテゴリの絞り込み、参加候補選択、ブランド配色、モバイル対応を追加 |
| 09:00-13:00 | Prompt 3を実行 | 差分と安全条件を確認し、人の承認後だけGitHub Pagesへ公開 |
| 13:00-15:00 | 公開URLを再読込 | HTTPS、4カード、絞り込み件数、参加候補2件を確認 |

見る場所はManager、Editor / Terminal、Browser、GitHub Pagesの4つに限定する。観客へはコード全文ではなく、各プロンプトの前後差分を見せる。

## 公開承認

Prompt 3は`git add`、commit、pushの前に必ず停止し、`公開してもよいですか？`と確認する。登壇者が正確に`公開して`と返答した場合だけ公開操作へ進む。

公開前に確認する項目:

1. remoteが公開専用リポジトリである。
2. 顧客情報、社員情報、認証情報、トークンが含まれない。
3. `SYNTHETIC_DATA_ONLY`が残っている。
4. 本番`mightylink-app.com`のリポジトリやFirebase設定を変更していない。

## 成功条件

- FILES: `index.html`、`styles.css`、`app.js`、画像が存在する。
- FUNCTION: カテゴリ件数が`4,1,1,1,1`、参加候補を2件選択できる。
- PUBLIC: GitHub PagesのHTTPS URLでタイトル、4カード、機能、画像を再確認できる。

## 90秒復旧

- 90秒間進展がなければ、その段階のライブ生成を止める。
- 完成版は`docs/demo/antigravity_workshop/output/index.html`を開く。
- Antigravityの説明は`BACKUP_PROMPTS.txt`の読み取り専用プロンプトへ切り替える。
- 公開が間に合わない場合は、GitHub Actionsの履歴と準備中ページを見せ、公開URLの検証項目を説明する。
- 会場で再インストール、認証再設定、本番リポジトリへの切替は行わない。

## 公式参照

- [Antigravity Browser](https://antigravity.google/docs/browser)
- [Antigravity Artifacts](https://antigravity.google/docs/artifacts)
- [Antigravity Permissions](https://antigravity.google/docs/permissions?app=antigravity)
- [GitHub Pagesの公開元設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHubのデプロイ履歴確認](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/view-deployment-history)
