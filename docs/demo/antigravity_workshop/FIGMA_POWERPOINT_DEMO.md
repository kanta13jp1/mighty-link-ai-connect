# Figma Slides -> PowerPoint 5分追加デモ

この手順は30分のAntigravity本編を変更せず、Q&Aまたは予備時間に追加する独立セグメントです。AIエージェントが構成を作り、Figma Slidesで編集可能なデザインへ変換し、PowerPointへ届ける流れを見せます。

## 採用構成

| 時刻 | 操作 | 成功の証拠 |
| --- | --- | --- |
| 00:00-00:30 | 目的と役割分担を説明 | `Prompt -> Figma Slides -> PPTX`を説明できる |
| 00:30-02:30 | `PROMPT_12_FIGMA_POWERPOINT.txt`を全文貼り付け | Figma Slides URLと3枚の編集可能なスライドが返る |
| 02:30-03:30 | Figmaで3枚を確認 | 文字切れ、重なり、秘密情報が0件 |
| 03:30-04:30 | `File -> Export slides to -> PPTX` | PPTXがダウンロードされる |
| 04:30-05:00 | PowerPointで開いて確認 | フォント、改行、色、静止画化を確認できる |

## 役割分担

- AIエージェント: 対象者、目的、構成、制約、完了条件をプロンプトへ固定する。
- Figma MCP / Figma Slides: 編集可能なスライド、レイアウト、配色、タイポグラフィを作る。
- PowerPoint: 配布形式へ変換し、変換後のフォント、改行、色、静止画化を最終確認する。

Figma MCPは完成品を自動保証する仕組みではなく、FigmaとAIエージェントの間で構造化されたデザイン文脈を受け渡す接続です。最終確認は人が行います。

## 事前準備

1. Codex AppでFigmaプラグインをインストールし、OAuth認証を完了する。
2. Figma側で使用するteam / planを1つに決める。現在の候補は`kanta13jp1's team`と`tokyofigma01`の2つなので、会場で選択しない。
3. Figma Slidesの作成、編集、URL表示までを一度リハーサルする。
4. `exports/mighty_skill_bridge_figma_powerpoint_demo_2026.pptx`を完成済み予備としてローカルに置く。
5. PowerPointの編集表示で`PROMPT_12_FIGMA_POWERPOINT.txt`全文をコピーできることを確認する。
6. 顧客情報、個人情報、APIキーをプロンプト、Figma、PowerPointへ入れない。

30分本編は引き続きAntigravityだけを使います。この5分追加デモだけは、Figma公式のCodex連携経路を利用します。

## 当日の操作

1. 補助PowerPointの「全文コピー」スライドを開く。
2. `PROMPT_12_FIGMA_POWERPOINT.txt`をCodex Appへ全文貼り付ける。
3. AIエージェントが返したFigma Slides URLを開く。
4. 3枚をグリッド表示し、タイトル、余白、文字切れ、重なりを確認する。
5. Figma Slidesで`Main menu -> File -> Export slides to`を開く。
6. File typeを`PPTX`、Structureを`editable PPTX equivalent`にして書き出す。
7. PowerPointで開き、フォント置換、改行、グラデーション、インタラクションの静止画化を確認する。

## 90秒復旧

- 30秒: Figma認証やteam選択を求められたらライブ作成を停止する。
- 60秒: リハーサル済みのFigma Slides URLを開く。
- 90秒: URLも開けなければ、完成済みPPTXへ切り替える。

会場ではFigmaの再認証、プラグイン再インストール、team変更を行いません。PPTX書き出しが失敗しても、Figma Slidesの画面と完成済みPPTXを使って説明を継続します。

## PowerPoint変換時の確認点

- PowerPointに無いフォントは既定フォントへ置き換わる可能性がある。
- Figma Slidesのグラデーションは単色へ変換される。
- インタラクションとコードブロックは静止画像になる。
- 書き出し後にPPTXが開けること、文字切れ0件、秘密情報0件を確認して完了とする。

## 公式資料

- Figma MCP: https://developers.figma.com/docs/figma-mcp-server/
- CodexへのRemote MCP設定: https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- Figma SlidesのPPTX書き出し: https://help.figma.com/hc/en-us/articles/24848334599447-Export-from-Figma-Slides
