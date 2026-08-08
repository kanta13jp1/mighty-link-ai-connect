# Google Antigravity 8/26ライブデモ運用手順

## 目的

2026年8月26日の社員向けAI研修で、Google Antigravityによる「指示、実行、確認」を15分で一度だけ実演する。機能を網羅する説明書ではなく、登壇者が迷わず、安全にデモを完走するための運用手順を正本とする。

## 成果物

- 投影資料: `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`（全12枚）
- 主プロンプト: `docs/demo/antigravity_workshop/MAIN_PROMPT.txt`
- 予備プロンプト: `docs/demo/antigravity_workshop/BACKUP_PROMPTS.txt`
- 合成入力データ: `docs/demo/antigravity_workshop/input/`
- 出力先: `docs/demo/antigravity_workshop/output/index.html`
- 事前検証: `python scripts/run_antigravity_live_demo.py`

## 前日までの確認

1. Antigravityを起動し、ログイン済みであることを確認する。
2. AntigravityからChromeを起動できることを確認する。Antigravityのブラウザは専用のChromeプロファイルを使用する。
3. このリポジトリをProjectとして開く。
4. `docs/demo/antigravity_workshop/input/`の3ファイルに`SYNTHETIC_DATA_ONLY`があることを確認する。
5. 次のコマンドが`PASS`になるまで投影を開始しない。

```powershell
python scripts/run_antigravity_live_demo.py
```

## 15分の進行

| 時刻 | 操作 | 観客に見せるもの |
| --- | --- | --- |
| 00:00-02:00 | `MAIN_PROMPT.txt`を貼り、出力先と禁止事項を読み上げる | 1 prompt |
| 02:00-07:00 | Plan、編集、必要な承認を一度だけ見せる | 1 file |
| 07:00-12:00 | `output/index.html`をブラウザで確認する | 1 browser |
| 12:00-15:00 | 変更、確認、未解決を3行で共有する | 1 report |

説明する画面はManager、Editor / Terminal、Artifacts / Browserの3か所だけとする。ログを逐語的に読み上げず、Plan、Edit、Browser、Reportの4場面だけを実況する。

## 承認と安全

- 入力は合成データだけを使用する。
- 書き込みは`docs/demo/antigravity_workshop/output/index.html`だけに限定する。
- 顧客、社員、認証情報を要求する操作は拒否する。
- 外部送信や別フォルダへの書き込みは拒否する。
- 権限ルールは公式仕様どおり`Deny > Ask > Allow`の優先順位で判断する。
- 対象と実行内容を説明できない承認は行わない。

## 成功条件

次の3点が見えたら追加依頼をせず、主デモを終了する。

1. `output/index.html`だけが変更されている。
2. 顧客課題、提案、適合スコア、次アクションが表示され、文字切れとモバイル幅を確認できる。
3. 最終回答が変更、確認、未解決の3行である。

## 90秒の復旧

- 進展が見えない: 現在地を一度だけ尋ねる。
- ブラウザが止まる: `output/index.html`を手動で開く。
- エラーが続く: `BACKUP_PROMPTS.txt`の読み取り専用デモへ切り替える。

会場で再インストール、モデルの連続変更、長時間のデバッグ、本番データや別Projectへの切り替えは行わない。

## 研修後

各参加者は、翌日から試す繰り返し業務を一つ選ぶ。合成または匿名化したデータで試し、役立ったプロンプトと人が確認した方法をセットで共有する。

## 公式参照

- [Google Antigravity documentation](https://antigravity.google/docs/)
- [Permissions](https://antigravity.google/docs/permissions?app=antigravity)
- [Browser](https://antigravity.google/docs/ide/browser)
- [Subagents](https://antigravity.google/docs/subagents)
- [Google Developers Blog: Build with Google Antigravity](https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/)
