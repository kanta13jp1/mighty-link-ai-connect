# Antigravity 8/26 AIエージェント学習サイト ライブデモキット

2026年8月26日の社内AI研修で、AIエージェントを使うと短時間でどこまで成果物を作れるかを見せる30分デモです。ライブ操作は低価格で利用しやすいAntigravityだけを使い、同じagent coreをAntigravity 2.0（IDE）、Antigravity CLI、Antigravity SDKの3つの操作面で見せます。Codex、Claude Code、Claude Cowork、Kiro、Antigravityの違いは学習サイトとPowerPointで比較します。

投影資料は`exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`です。PowerPointから全文をコピー＆ペーストできるプロンプト、事前準備、Skill導入、GitHub Pages公開、リハーサル後の復元、90秒復旧を記載します。

## ゴール

観客が「AIエージェントは、要件整理、専門能力の追加、制作、検証、外部サービス連携、公開までを一つの流れとして進められる」と理解することがゴールです。学習サイト自体は研修教材ではなく、短時間でも完成度の高い成果物を作れることを示すデモ成果物です。

## 30分のデモ

| 時刻 | 操作 | 見せるもの |
| --- | --- | --- |
| 00:00-02:00 | ゴールと5製品比較 | ライブ操作をAntigravityへ絞る理由 |
| 02:00-05:00 | `/grill-me` | 実装前の質問、推奨案、成功条件の確定 |
| 05:00-08:00 | `/find-skills` + Skill導入 | 品質比較とproject-local導入 |
| 08:00-14:00 | IDEで初版作成 | 会話、計画、コード、Browserを一画面で見る |
| 14:00-18:00 | IDEでSkill適用 | デザイン、絞り込み、2製品比較、2 viewport |
| 18:00-21:00 | Antigravity CLI | 同じrepoをターミナルから読み取り監査 |
| 21:00-24:00 | Antigravity SDK | Pythonからread-only agentを実行し結果をstream表示 |
| 24:00-26:00 | MCP確認 | GitHubを読み取り専用確認 |
| 26:00-30:00 | Pages公開 + Proof | 明示承認、push、HTTPS、操作結果 |

残り30分は質疑応答と予備時間です。Q&Aでは、時間と質問に応じて公式動画、Nano Banana実画像、Screenshot Artifactへの位置指定コメントを扱います。90秒以上進展が見えない工程は停止し、完成済みローカル成果物またはバックアッププロンプトへ切り替えます。

## プロンプト

1. `PROMPT_00_GRILL_ME.txt`: 最大2問で要件と成功条件を確定する。
2. `PROMPT_01_FIND_SKILLS.txt`: `/find-skills`で候補を検索し、品質を比較する。
3. `PROMPT_02_INSTALL_SKILL.txt`: `frontend-design`をプロジェクト単位で導入し、内容を確認する。
4. `PROMPT_03_BUILD.txt`: JavaScriptなしの初版学習サイトを作る。
5. `PROMPT_04_APPLY_SKILL.txt`: `/frontend-design`を使い、見た目と比較機能を改善する。
6. `PROMPT_05_MCP_CHECK.txt`: GitHub MCPを読み取り専用で確認する。
7. `PROMPT_06_PUBLISH.txt`: 人の明示承認後だけGitHub Pagesへ公開する。
8. `PROMPT_07_OFFICIAL_VIDEO.txt`: 動画の公式性を照合してから埋め込むQ&A用プロンプト。
9. `PROMPT_08_NANO_BANANA.txt`: Nano Banana 2を使う画像生成Toolで実画像を1枚作るQ&A用プロンプト。
10. `PROMPT_09_VISUAL_FEEDBACK_COMMENT.txt`: Screenshot Artifactへ位置指定コメントを残すQ&A用プロンプト。
11. `PROMPT_10_CLI_READONLY.txt`: Antigravity CLIへ貼り付け、同じrepoを読み取り専用で監査する本編用プロンプト。
12. `PROMPT_11_SDK_READONLY.txt`: Antigravity SDKから実行する読み取り専用の本編用プロンプト。
13. `antigravity_sdk_readonly.py`: SDKをread-only toolsだけで動かし、結果をstream表示する実行ファイル。

Prompt 7-9は30分本編に含めません。リハーサルでは公開後の追加改善だけで約78分かかったため、Q&Aまたは予備時間に限定します。

## 事前準備

専用リポジトリ`kanta13jp1/mighty-link-antigravity-live-demo`をAntigravityで開きます。GitHub Pagesは`main`の`/(root)`から公開するよう事前設定し、公開URLを`https://kanta13jp1.github.io/mighty-link-antigravity-live-demo/`に固定します。

デモ開始前に次を確認します。

- Antigravityにサインイン済みで、専用リポジトリだけを開いている。
- Antigravity CLIの`agy`をインストールし、専用repoで対話TUIを一度起動してサインイン、表示テーマ、workspace trustを完了している。`/permissions`で対象4ファイルの読み取りだけを事前承認し、書き込み、command、URLアクセスは承認しない。
- 専用のPython仮想環境へ`google-antigravity`をインストールし、`GEMINI_API_KEY`を安全な環境変数として設定した上で、`antigravity_sdk_readonly.py --dry-run`と実行リハーサルを完了している。
- `git remote -v`が専用リポジトリ、現在branchが`main`である。
- Node.js、Git、`npx skills`、ブラウザが利用できる。
- workspace Skillの`/grill-me`と`/find-skills`がSlash Commandへ表示される。
- `frontend-design`はまだインストールされていない。
- GitHub MCPは接続済みなら使用し、未接続なら会場で認証しない。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`があり、秘密情報と個人情報がない。
- 製品数が5件で、料金、クォータ、診断、検索、エクスポート、テーマ切替がない。
- PowerPointを編集表示で開き、各プロンプトを全文コピーできる。

```powershell
python scripts/run_antigravity_live_demo.py
```

CLIとSDKの導入・認証は本番中に行いません。Windowsでの事前準備は次のとおりです。

```powershell
irm https://antigravity.google/cli/install.ps1 | iex
agy --version

python -m venv .venv-antigravity-sdk
.\.venv-antigravity-sdk\Scripts\Activate.ps1
python -m pip install --upgrade pip google-antigravity
python .\antigravity_sdk_readonly.py --workspace . --dry-run
```

API keyや認証tokenはPowerPoint、repo、コマンド履歴へ記載しません。現在のPCではSDK packageの導入とdry-runまでは検証済みですが、実通信には`GEMINI_API_KEY`の事前設定が必要です。本番中にCLIまたはSDKが認証を要求した場合はその場で認証せず、リハーサル済み画面へ切り替えます。

CLI本番は対話TUIの`agy`を使います。非対話の`agy -p`はAsk権限を確認できず自動拒否されるため、リハーサルでも本番でも使いません。`--dangerously-skip-permissions`も使いません。

## IDE・CLI・SDKの見せ分け

- **Antigravity 2.0（IDE）**: 要件、計画、コード差分、Browser、Screenshot Artifactを一画面で見ながら作る。
- **Antigravity CLI**: `agy`のTUIへ`PROMPT_10_CLI_READONLY.txt`を全文貼り付け、同じrepoを短く監査する。ファイル変更はさせない。
- **Antigravity SDK**: Pythonコードでagentのsystem instructionsとread-only toolsを固定し、`PROMPT_11_SDK_READONLY.txt`を自動投入してstream結果を表示する。

CLI本番操作:

```powershell
agy
```

起動後、PowerPointのCLIプロンプトを全文貼り付けます。SDK本番操作:

```powershell
.\.venv-antigravity-sdk\Scripts\Activate.ps1
python .\antigravity_sdk_readonly.py --workspace .
```

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

- Prompt 4で製品数、変更ファイル、追加禁止機能を固定する。
- Prompt 7でYouTubeのtitle、author_name、author_urlを確認してから「公式」と表示する。
- Prompt 8で画像生成Toolが使えた場合だけNano Banana利用として説明する。
- Prompt 9でAntigravityのScreenshot Artifactへ位置指定コメントを残し、重なりだけを修正する。
- サイト内のVisual FeedbackシミュレーターをAntigravity本体の機能実演として扱わない。

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

## 停止条件

- 専用リポジトリ以外が開かれている。
- remote、branch、Pages URLのいずれかが予定と違う。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`がない。
- 追跡対象に認証情報、トークン、個人情報、顧客情報が含まれる。
- Skillの公開元またはインストール先を確認できない。
- 登壇者が正確に「公開して」と回答していない。
- 90秒以上、画面上の進展がない。

停止時は会場で認証、設定変更、force pushを行わず、`BACKUP_PROMPTS.txt`とローカル完成版へ切り替えます。
