# Antigravity 8/26 AIエージェント学習サイト ライブデモキット

2026年8月26日の社内AI研修で、AIエージェントを使うと短時間でどこまで成果物を作れるかを見せる30分デモです。ライブ操作は低価格で利用しやすいAntigravityだけを使い、IDEではなく独立したデスクトップアプリのAntigravity 2.0からWebサイトの要件整理、テスト仕様、実装、Browser検証、GitHub Pages公開まで進めます。MCPの実演ではFigma remote MCPを使い、3枚のFigma Slidesを編集可能なPowerPointへ書き出します。Codex、Claude Code、Claude Cowork、Kiro、Antigravityの違いは学習サイトとPowerPointで比較します。

投影資料は`exports/mighty_skill_bridge_antigravity2_figma_mcp_powerpoint_demo_2026.pptx`です。PowerPointから全文をコピー＆ペーストできるプロンプト、事前準備、Skill導入、Figma MCP、GitHub Pages公開、リハーサル後の復元、90秒復旧を記載します。元資料は上書きしません。

## ゴール

観客が「AIエージェントは、要件整理、テスト仕様、専門能力の追加、Web制作、検証、MCPによる外部サービス連携、公開までを一つの流れとして進められる」と理解することがゴールです。学習サイトと3枚のPowerPointは、短時間でも複数のToolをまたぐ完成度の高い成果物を作れることを示すデモ成果物です。

30分後の到達目標は次の3点です。

1. AIエージェントが、期待動作をテストで固定し、計画、Tool実行、証拠確認までつなぐことを説明できる。
2. SkillとMCPの違いを、仕事の型と外部Toolへの接続として説明できる。
3. 目的、境界、証拠、承認を人が持つことで、安全に仕事を任せられる。

## MIXI研修を参考にした進行設計

[MIXI 26新卒技術研修のAI研修Day1](https://www.youtube.com/watch?v=da7hWlccpxw)と[MIXI公式レポート](https://mixi.co.jp/news/2026/0727/55293/)を参考に、資料説明中心ではなく、短い説明と実行を往復する構成へ変更しました。研修内容やスライド表現を転載するのではなく、次の進行原則だけを本デモへ適用します。

- 冒頭で具体的な到達目標を示し、最後に同じ項目へ戻る。
- 開始時に「AIエージェントでファイルを変更した経験は？」と挙手で確認し、説明速度を調整する。
- 各ブロックを`説明30秒以内 → 実行 → 証拠確認 → 一言で言語化`の順で進める。
- 出力、差分、Browser、件数、権限、HTTPSなど、見るべき証拠を操作前に一つだけ予告する。
- 成果物の派手さだけで終わらせず、人の責任と実務での使い所へ接続する。

実演直後は毎回、講師が「今、何を任せ、どの証拠で成功と判断しましたか？」と問い、3秒置いてから答えを短く回収します。

## 30分のデモ

| 時刻 | 操作 | 見せるもの | 直後に確認すること |
| --- | --- | --- | --- |
| 00:00-02:00 | ゴールと5製品比較 | ライブ操作をAntigravityへ絞る理由 | 3つの到達目標と参加者の経験値 |
| 02:00-04:00 | `/grill-me` | 実装前の質問、推奨案、成功条件の確定 | `DECISIONS`に境界と成功条件がある |
| 04:00-07:00 | `/find-skills` + Skill導入 | 品質比較とproject-local導入 | 公開元、監査、導入先を説明できる |
| 07:00-10:00 | Antigravity 2.0でテスト仕様作成 | `TEST_SPEC.md`と契約テストを先に作る | サイト未作成でREDになる |
| 10:00-15:00 | Antigravity 2.0で初版作成 | テストを変えずにHTML/CSSを実装 | T01-T05 PASS、T06-T08 FAILになる |
| 15:00-20:00 | Skill適用 + Browser検証 | 絞り込み、2製品比較、2 viewport | 自動8件とBrowser確認がGREENになる |
| 20:00-25:00 | Figma MCP + PowerPoint | 3枚のFigma Slidesを作り、編集可能PPTXへ書き出す | team、project、3枚、編集可能テキストを確認できる |
| 25:00-30:00 | Pages公開 + Proof | 明示承認、push、HTTPS、操作結果 | 8 tests、HTTPS、5製品、2件比較、最新commitが一致する |

残り30分は質疑応答と予備時間です。Q&Aでは、時間と質問に応じてAntigravity CLI / SDKの違い、公式動画、Nano Banana実画像、Screenshot Artifactへの位置指定コメントを扱います。90秒以上進展が見えない工程は停止し、完成済みローカル成果物またはバックアッププロンプトへ切り替えます。

Figma MCPの5分セグメントは本編に含めます。全文プロンプト、PPTX書き出し、変換制約、90秒復旧は[`FIGMA_POWERPOINT_DEMO.md`](FIGMA_POWERPOINT_DEMO.md)に固定します。

## プロンプト

1. `PROMPT_00_GRILL_ME.txt`: 最大2問で要件と成功条件を確定する。
2. `PROMPT_01_FIND_SKILLS.txt`: `/find-skills`で候補を検索し、品質を比較する。
3. `PROMPT_02_INSTALL_SKILL.txt`: `frontend-design`をプロジェクト単位で導入し、内容を確認する。
4. `PROMPT_03_TEST_SPEC.txt`: サイトより先にテスト仕様書と8件の契約テストを作り、REDを確認する。
5. `PROMPT_03_BUILD.txt`: テストを変えず、JavaScriptなしの初版を作って基本5件をPASSさせる。
6. `PROMPT_04_APPLY_SKILL.txt`: `/frontend-design`で比較機能を実装し、自動8件をGREENにする。
7. `PROMPT_05_MCP_CHECK.txt`: Figma MCPのaccount、team、project、Slides書き込みToolを読み取り確認する。
8. `PROMPT_06_PUBLISH.txt`: 人の明示承認後だけGitHub Pagesへ公開する。
9. `PROMPT_07_OFFICIAL_VIDEO.txt`: 動画の公式性を照合してから埋め込むQ&A用プロンプト。
10. `PROMPT_08_NANO_BANANA.txt`: Nano Banana 2を使う画像生成Toolで実画像を1枚作るQ&A用プロンプト。
11. `PROMPT_09_VISUAL_FEEDBACK_COMMENT.txt`: Screenshot Artifactへ位置指定コメントを残すQ&A用プロンプト。
12. `PROMPT_10_CLI_READONLY.txt`: Q&AでAntigravity CLIの違いを示す読み取り専用プロンプト。
13. `PROMPT_11_SDK_READONLY.txt`: Q&AでAntigravity SDKの違いを示す読み取り専用プロンプト。
14. `antigravity_sdk_readonly.py`: SDKをread-only toolsだけで動かす参考実装。
15. `PROMPT_12_FIGMA_POWERPOINT.txt`: 本編でFigma MCPから3枚のFigma Slidesを作るプロンプト。

## テスト駆動の見せ方

本編の状態遷移は`RED -> 部分PASS -> GREEN`で固定する。

Prompt 3Aではサイトファイルを作らず、`TEST_SPEC.md`と`tests/test_site_contract.py`だけを作る。テスト実行がREDになることを「失敗」ではなく「実装前に期待値を固定できた証拠」として示す。

Prompt 3Bではテストを編集せずに初版を作り、T01-T05のPASSとT06-T08のFAILを見せる。Prompt 4では残りの機能を追加し、自動8件のGREENとT09の2 viewport確認を揃える。公開後のT10まで同じ仕様書で追跡する。

```powershell
python -m unittest discover -s tests -v
```

Prompt 7-9は30分本編に含めません。リハーサルでは公開後の追加改善だけで約78分かかったため、Q&Aまたは予備時間に限定します。

## 事前準備

専用リポジトリ`kanta13jp1/mighty-link-antigravity-live-demo`をAntigravity 2.0の専用Projectへ登録します。GitHub Pagesは`main`の`/(root)`から公開するよう事前設定し、公開URLを`https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/`に固定します。

デモ開始前に次を確認します。

- Antigravity 2.0にサインイン済みで、デモ専用Projectだけを開いている。
- Projectへ登録されたfolderが専用リポジトリだけで、Project permissionsがデモ範囲に限定されている。
- `git remote -v`が専用リポジトリ、現在branchが`main`である。
- Node.js、Git、`npx skills`、ブラウザが利用できる。
- workspace Skillの`/grill-me`と`/find-skills`がSlash Commandへ表示される。
- `frontend-design`はまだインストールされていない。
- Figma remote MCPはAntigravity 2.0で接続済みで、会場では再認証しない。
- Figma作成先が`kanta13jp1's team / Team project`、project IDが`264549730`である。
- Figma Slidesの作成、3枚確認、editable PPTX equivalent書き出しをリハーサル済みである。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`があり、秘密情報と個人情報がない。
- 製品数が5件で、料金、クォータ、診断、検索、エクスポート、テーマ切替がない。
- PowerPointを編集表示で開き、各プロンプトを全文コピーできる。
- 完成済みのFigma Slides URLと予備PPTXを開ける。
- Python 3で`unittest`を実行でき、外部テストライブラリを追加しない。

```powershell
python scripts/run_antigravity_live_demo.py
```

API keyや認証tokenはPowerPoint、repo、コマンド履歴へ記載しません。Figma OAuth、MCP接続、team、project、利用上限は会場入り前に確認します。本番中に認証を要求された場合はその場で認証せず、リハーサル済みFigma Slidesまたは予備PPTXへ切り替えます。

## 本編で使う操作面

- **Antigravity 2.0**: IDEから独立したデスクトップアプリ。Project内で要件、計画、Tool実行、ファイル差分、Browser、Artifactsを確認しながらWeb制作を進める。
- **Figma MCP**: Antigravity 2.0からFigmaのaccount、team、project、Slidesへ接続し、3枚の編集可能な資料を作る。
- **Figma Slides / PowerPoint**: Figmaで視覚と構造を確認し、editable PPTX equivalentとして書き出してPowerPointで最終確認する。

Antigravity IDE、CLI、SDKは30分本編では操作しません。違いを質問された場合だけQ&Aで説明します。

## 事前導入する2つのSkill

`/grill-me`と`/find-skills`はデモを進めるための基礎Skillなので、専用リポジトリの`.agents/skills/`へ事前に配置します。ライブでインストールするのは`frontend-design`だけです。

`/find-skills`はSkills CLIとskills.shを使ってSkill候補を探し、インストール数だけでなく、公開元、GitHub実績、監査情報、導入コマンドを確認するSkillです。

## ライブ導入するSkill

`anthropics/skills@frontend-design`を採用します。Web画面の情報設計、タイポグラフィ、配色、余白、動き、レスポンシブ品質を改善するAnthropic公式Skillで、導入前後の差が観客へ伝わりやすいためです。

```powershell
npx skills add anthropics/skills@frontend-design --agent antigravity --copy -y
npx skills list --json
```

グローバル導入を示す`-g`は使いません。Skillは専用リポジトリの`.agents/skills/frontend-design/`だけへコピーし、リハーサル後に削除できるようにします。インストールしたSkillはエージェントと同等の権限で指示やスクリプトを実行し得るため、使用前に`SKILL.md`と公開元を確認します。

## 用語の扱い

- Kiroの`Steering`は、`.kiro/steering/`などのMarkdownでプロジェクト知識や規約を持続させる正式機能です。
- Kiroの`Powers`は、`POWER.md`、MCP設定、任意のSteeringやHooksをまとめ、必要時だけ動的に有効化する正式機能です。
- AntigravityにはRules、Workflows、Skills、MCP、Artifactsがあります。Kiroの正式機能名としてのSteeringやPowersがAntigravityにあるとは説明しません。
- SkillsとMCPは複数製品で採用される共通概念ですが、保存場所、呼び出し方、権限モデルは製品ごとに異なります。

詳しい比較は`DEMO_CONCEPTS.md`を参照します。

## 2026年8月9日の実リハーサル

専用repoの初回公開`05cfa7c`から最終改善`347ce89`まで11コミット、約78分で、GitHub Pagesへの公開、Google Antigravity公式動画、9製品、Visual Feedback模擬体験、Nano Bananaテーマ模擬、検索、比較、暗色デザインまで実装できました。公開URLはデスクトップ1440x900とモバイル390x844で横スクロール0でした。

一方で、要件の5製品から9製品へ広がり、除外していた料金・クォータ・診断・検索・エクスポート・テーマ切替まで追加されました。Nano Bananaは画像生成ToolではなくCSSテーマ切替として模擬され、固定比較サマリーが下部の内容を隠す状態も確認しました。

本番では次のように修正します。

- Prompt 3Aでテスト仕様を実装前に固定し、Prompt 3BとPrompt 4ではテストを変更しない。
- Prompt 4で製品数、変更ファイル、追加禁止機能を固定する。
- Prompt 7でYouTubeのtitle、author_name、author_urlを確認してから「公式」と表示する。
- Prompt 8で画像生成Toolが使えた場合だけNano Banana利用として説明する。
- Prompt 9でAntigravityのScreenshot Artifactへ位置指定コメントを残し、重なりだけを修正する。
- サイト内のVisual FeedbackシミュレーターをAntigravity本体の機能実演として扱わない。

## 2026年8月13日の比較サイト再検証

[公開サイト](https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/)を、リハーサルで広がった9製品から本来の5製品へ戻し、単純な機能一覧ではなく実務選定に使える比較へ再構成しました。

- 公式配布元から取得したCodex、Claude Code、Claude Cowork、Kiro、Antigravityのアイコンをローカル配信する。
- 版番号を`Codex CLI 0.147.0`、`Claude Code 2.1.229`、`Kiro IDE 1.0.293`、`Antigravity 2.8.0`として公式Changelogと照合する。
- Claude Coworkはモデル版を代用せず、`公開版番号なし（SaaS）`と表示する。
- 各製品に最新更新、最新公式動画、最新公式ブログ、確認日、一次情報リンクを表示する。
- 操作面、持続指示、拡張、MCP、Browser、並列実行、SDK、証拠、安全境界、料金、導入注意を含む13軸で最大2製品を比較する。
- 10回の自己レビューを`output/SELF_REVIEW.md`へ残し、公式出典を`output/SOURCE_AUDIT.md`、アイコン由来を`output/ICON_SOURCES.md`へ記録する。

完成版はPython契約テスト11件とNode DOM E2E 6件を通過しました。Chromiumの320、390、768、1024、1440pxでページ横はみ出しがなく、公開URLでも5アイコン、40出典リンク、13比較行、コンソールエラー0件を確認済みです。

## リハーサル後の復元

リハーサルで公開した最初と最後のcommitを控え、公開確認後にその範囲を`git revert --no-commit`して1件の復元commitをpushします。履歴を壊す`git reset --hard`やforce pushは使いません。

```powershell
npx skills remove frontend-design --agent antigravity -y
$skillsRoot = (Resolve-Path .agents/skills).Path
$skillPath = Join-Path $skillsRoot 'frontend-design'
if (Test-Path -LiteralPath $skillPath) {
  $resolvedSkillPath = (Resolve-Path -LiteralPath $skillPath).Path
  if ((Split-Path $resolvedSkillPath -Parent) -ne $skillsRoot) { throw 'Unexpected Skill path' }
  Remove-Item -LiteralPath $resolvedSkillPath -Recurse -Force
}
if (Test-Path -LiteralPath .\skills-lock.json) { Remove-Item -LiteralPath .\skills-lock.json -Force }
npx skills list --json
git revert --no-commit <リハーサル前BASELINE>..<最後のリハーサルcommit SHA>
git commit -m "Restore Antigravity rehearsal baseline"
git push origin main
```

`--copy`で導入したSkillは、Skills CLIの`remove`後もフォルダーと`skills-lock.json`が残る場合があります。そのため、専用repoの`.agents/skills`直下であることを検証してから残存ファイル、空フォルダー、今回だけ生成されたlock fileを削除します。復元後は`npx skills list --json`で`frontend-design`がないこと、公開URLが「準備中」へ戻ったこと、`git status --short`が空であることを確認します。`/grill-me`と`/find-skills`は本番でも使うため削除しません。

Figma側は、リハーサルで作成したファイル名とURLを記録し、本番用の予備ファイルと区別します。リハーサル専用ファイルだけをFigmaのTrashへ移動し、team、project、MCP接続、予備ファイルは残します。共有中または用途不明のファイルは削除しません。

## 停止条件

- 専用リポジトリ以外が開かれている。
- remote、branch、Pages URLのいずれかが予定と違う。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`がない。
- 追跡対象に認証情報、トークン、個人情報、顧客情報が含まれる。
- Skillの公開元またはインストール先を確認できない。
- Figma account、team、project IDのいずれかが予定と違う。
- Figma MCPのSlides書き込みToolがない、利用上限に達した、またはOAuth再認証を要求された。
- 登壇者が正確に「公開して」と回答していない。
- 90秒以上、画面上の進展がない。

停止時は会場で認証、設定変更、force pushを行わず、`BACKUP_PROMPTS.txt`とローカル完成版へ切り替えます。
