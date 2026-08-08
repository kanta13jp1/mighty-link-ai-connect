# Antigravity 8/26 段階開発ライブデモキット

2026年8月26日の社内AI研修で、1つのWebサイトを3本のプロンプトで作成、改善、公開するためのデモキットです。入力と画像は公開可能な合成素材だけを使用します。

## デモの流れ

1. 専用リポジトリ`kanta13jp1/mighty-link-antigravity-live-demo`をAntigravityのProjectとして開く。
2. `MAIN_PROMPT.txt`で情報サイトを作り、ブラウザで初版を確認する。
3. `PROMPT_02_IMPROVE.txt`でカテゴリ絞り込み、参加候補、デザイン変更を追加する。
4. `PROMPT_03_PUBLISH.txt`で差分と公開範囲を確認し、登壇者が「公開して」と答えた後だけGitHub Pagesへpushする。
5. 公開URLをブラウザで開き、HTTPS、表示、機能を確認する。

## 事前準備

専用リポジトリには、`SITE_BRIEF.md`、3本のプロンプト、`assets/workshop-hero.png`だけを配置し、GitHub Pagesの公開元を`main`の`/(root)`に設定します。現行プロダクトのリポジトリやFirebase Hostingは使用しません。

```powershell
python scripts/run_antigravity_live_demo.py
```

検証は、段階性、初版の境界、機能追加、デザイン変更、公開先分離、人の承認、秘密情報防止、公開後確認、復旧性、資料整合の10仮説をfail-closedで判定します。

## 停止条件

- 専用リポジトリ以外が開かれている。
- `SITE_BRIEF.md`に`SYNTHETIC_DATA_ONLY`がない。
- 追跡対象に認証情報、個人情報、顧客情報が含まれる。
- 登壇者が正確に「公開して」と回答していない。
- 90秒以上進展が見えない。

停止時は会場でデバッグを続けず、`BACKUP_PROMPTS.txt`の読み取り専用デモとローカル完成版へ切り替えます。
