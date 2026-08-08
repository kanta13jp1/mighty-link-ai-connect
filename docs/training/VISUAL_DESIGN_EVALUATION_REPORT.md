# Antigravity研修資料 視認性・デモ効率評価

## 対象

- `exports/mighty_skill_bridge_antigravity_user_guide_2026.pptx`
- 16:9、全12枚、2026年8月8日評価

根拠のない点数評価は行わない。投影時の読みやすさ、画像の判読性、当日の進行効率を、実装値と検査結果で判定する。

## 評価結果

| 評価軸 | 確認した証拠 | 判定 |
| --- | --- | --- |
| 第一印象 | 表紙で研修日、製品名、ライブデモを第一視認に配置 | PASS |
| ブランド | MightyLINK公式サイトの青`#00A5E3`と橙`#EF7E00`をアクセントに使用 | PASS |
| タイトル | 表紙68 px、各ページ48 px。長い見出しも1行または意図した改行で収容 | PASS |
| 本文 | 主本文24-30 px。投影対象のプロンプトは25 px | PASS |
| 余白 | 1280 x 720の固定キャンバスで、左右68 px以上の基準余白を維持 | PASS |
| 画像 | 公式画像を5枚に限定し、同一画像の反復を廃止 | PASS |
| 画像サイズ | UI画像は各ページの約40-55%幅で配置し、見せたい領域を1画面に限定 | PASS |
| 情報密度 | 1ページ1判断。長い説明書を12枚のデモ進行へ圧縮 | PASS |
| デモ導線 | 15分の時刻、主プロンプト、成功条件、90秒復旧を別ページで即参照可能 | PASS |
| 編集可能性 | 元PPTXをArtifact Toolで取り込み、継承要素を編集して再出力 | PASS |

## 使用画像

| ページ | 画像 | 出典 |
| --- | --- | --- |
| 1 | Antigravity公式プロダクトアート | Google Developers Blog |
| 4 | Project / Worktree選択UI | Google Antigravity公式ドキュメント |
| 5 | Editor + Manager UI | Google Developers Blog |
| 7 | Agentsパネル | Google Antigravity公式ドキュメント |
| 8 | Review Policy UI | Google Antigravity公式ドキュメント |

外部画像と非自明な仕様は、該当ページのスピーカーノートに`[Sources]`として記録した。

## 検査証跡

- 12枚を原寸PNGで個別に目視確認: PASS
- `slides_test.py`: `Test passed. No overflow detected.`
- `check_template_fidelity.mjs`: `status=pass`, `issueCount=0`
- `python scripts/run_antigravity_live_demo.py`: PASS
- `py -m pytest tests/test_antigravity_live_demo.py -q -s`: 2件PASS

## 残余リスク

AntigravityのUIと利用可能なモデルは更新され得る。8月26日朝にログイン、Chrome起動、Project選択、主プロンプトの限定出力を再確認する。UI差分があっても、15分進行と90秒復旧の判断基準は変更しない。

## 判定

社長事前確認と会場投影に使用できる。承認条件は、当日朝のデモキット検証がPASSであること、合成データだけを使用すること、90秒で予備デモへ切り替えることの3点とする。
