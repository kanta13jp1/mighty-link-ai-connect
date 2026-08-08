# Antigravity 8/26 ライブデモキット

このフォルダは、2026年8月26日のMightyLINK社内AI研修で使う専用デモ環境です。入力データはすべて架空の合成データです。顧客情報、社員情報、認証情報を追加しないでください。

## 当日の主デモ

1. リポジトリをAntigravityのProjectとして開く。
2. `MAIN_PROMPT.txt`をそのまま入力する。
3. `output/index.html`だけが作成されたことを確認する。
4. ブラウザで4項目、文字切れ、モバイル幅を確認する。
5. 変更ファイル、確認結果、未解決点の3行報告で終了する。

事前確認:

```powershell
python scripts/run_antigravity_live_demo.py
```

90秒以上進展が見えない場合はデバッグを続けず、`BACKUP_PROMPTS.txt`の読み取り専用デモへ切り替えます。
