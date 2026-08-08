# Antigravity 8/26 ライブデモキット

このフォルダは、2026年8月26日のMightyLINK社内AI研修で使う専用デモ環境です。入力データはすべて架空の合成データです。顧客情報、社員情報、認証情報を追加しないでください。

## 当日の主デモ

1. リポジトリをAntigravityのProjectとして開く。
2. `MAIN_PROMPT.txt`をそのまま入力する。
3. `output/index.html`だけが作成されたことを確認する。
4. ブラウザで1440x900と390x844を開き、4項目、文字切れ、スクロール幅を確認する。
5. 変更ファイル、確認結果、未解決点の3行報告で終了する。

事前確認:

```powershell
python scripts/run_antigravity_live_demo.py
```

検証は、入力一致、意思決定表示、視線順序、ブランド、スコア説明、人の確認、安全、デスクトップ、モバイル、アクセシビリティの10仮説をfail-closedで判定します。詳細は`DEMO_HYPOTHESIS_REPORT.md`を参照してください。

90秒以上進展が見えない場合はデバッグを続けず、`BACKUP_PROMPTS.txt`の読み取り専用デモへ切り替えます。
