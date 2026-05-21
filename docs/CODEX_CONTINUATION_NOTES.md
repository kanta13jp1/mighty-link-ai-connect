# Codex 継続作業メモ

作成日: 2026-05-21

## 背景

Antigravity で利用している Gemini 側で baseline quota 制限が発生したため、2026/5/27 18:48:10 の quota refresh までは VSCode + Codex で実装・整理・検証を継続する。

表示された制限メッセージ:

```text
Your plan's baseline quota will refresh on 2026/5/27 18:48:10.
```

## 現在の運用方針

- Antigravity + Gemini の quota が残っている通常時は、Antigravity を主作業環境として使う。
- Antigravity 側で Gemini quota 制限に達したら、VSCode + Codex に切り替えて開発を継続する。
- コード実装、ドキュメント整備、ローカル検証、Git 操作は Codex で継続する。
- FastAPI アプリは Gemini API が使えない場合でも mock fallback で動作する。
- Google Sheets / Calendar / Drive 連携は `authorized_user.json` を使い、Workspace アカウント `k-umezawa@ml-mightylink.com` で継続する。
- Gemini API の quota を消費したくない場合は `AI_FORCE_MOCK=1` を付けてサーバーを起動する。

## VSCode + Codex への切り替え手順

1. VSCode で本プロジェクト `mighty-link-ai-connect` を開く。
2. Codex に作業を引き継ぎ、実装・検証・ドキュメント更新を進める。
3. Gemini quota 中は `AI_FORCE_MOCK=1` で FastAPI を起動し、AI fallback と Sheets 連携の確認を行う。
4. 作業完了後は Codex で commit / push / main 反映まで行う。

## quota-safe 起動

PowerShell:

```powershell
$env:AI_FORCE_MOCK = "1"
python src/app.py
```

バックグラウンド起動:

```powershell
$env:AI_FORCE_MOCK = "1"
Start-Process -WindowStyle Hidden -FilePath python -ArgumentList "src/app.py" -WorkingDirectory .
```

## 確認方法

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health
```

期待値:

```json
{
  "status": "healthy",
  "sheets_live": true,
  "gemini_live": false,
  "ai_mode": "deterministic_fallback",
  "ai_force_mock": true
}
```

## Gemini 復帰時

quota refresh 後に live Gemini を使う場合は、`AI_FORCE_MOCK` を未設定に戻し、`GEMINI_API_KEY` を設定してから `python src/app.py` を起動する。

## 2026-05-21 作業ログ: バックエンド AI 基盤肉付け

Gemini quota 復帰待ちの間に、VSCode + Codex で `src/app.py` の AI fallback を固定 mock から deterministic pipeline へ拡張した。

実施内容:

- `ParsedProfile` データ構造を追加。
- スキル分類辞書 `SKILL_TAXONOMY` を追加。
- `/api/parse` で structured profile を返すようにした。
- `/api/match` で matched skills / missing skills / 4軸スコア根拠を含む structured payload を返すようにした。
- Gemini live 復帰時に deterministic pre-parse / pre-score を prompt context として渡す準備を入れた。
- カレンダー同期スクリプトを冪等化し、既存イベントを更新して重複作成しにくい動きにした。
- WBS に `T304` を追加し、Google Sheets の `Mighty-Link WBS` タブへ同期した。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ同期した。時間指定イベントの比較を正規化し、重複していた社長報告会イベントを整理したうえで、最終結果は `Success: 6, Updated: 6, Failed: 0`。

関連ドキュメント:

- [BACKEND_AI_PIPELINE.md](BACKEND_AI_PIPELINE.md)
- [WBS.md](WBS.md)

## 2026-05-21 作業ログ: AI監査ログと再同期

deterministic pipeline の判定根拠を後から確認・改善できるよう、`src/app.py` にローカル監査ログ基盤を追加した。

実施内容:

- `/api/parse` と `/api/match` のレスポンスに `audit_event_id` を追加。
- `data/audit/ai_audit.jsonl` へ、AI mode、スコア、matched/missing skills、短い excerpt、digest を保存するようにした。
- 原文全文は保存せず、監査ログ本体 `data/audit/*.jsonl` は `.gitignore` 対象にした。
- `data/audit/.gitkeep` を追加し、ログ保存先ディレクトリのみ Git 管理できるようにした。
- `/api/audit/recent?limit=10` を追加し、直近の AI 判定イベントを確認できるようにした。
- 英語入力の `8 years experience` も経験年数として抽出できるよう、経験年数パーサーを拡張した。
- WBS に `T305` を追加し、AI監査基盤の実装完了を反映した。

検証結果:

- `python -m compileall src scripts` 成功。
- `AI_FORCE_MOCK=1` で FastAPI を起動し、`/api/health` が `ai_mode: deterministic_fallback` を返すことを確認。
- `/api/parse` が `structured_profile.experience_years: 8` と `audit_event_id` を返すことを確認。
- `/api/match` が `final_score: 97`、`matched_skills`、`missing_skills`、`audit_event_id` を返すことを確認。
- `/api/audit/recent?limit=3` が直近監査イベントを返すことを確認。
- Google Sheets の `Mighty-Link WBS` タブへ WBS 14 行を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 6, Updated: 6, Failed: 0`。

## 2026-05-21 作業ログ: 公開デモURL保護

社長共有済みの公開URL `https://kanta13jp1.github.io/mighty-link-ai-connect/` が README fallback になるデグレを防ぐため、GitHub Pages root 配信を明示的に保護した。

実施内容:

- root `index.html` が GitHub Pages の公開デモ本体であることを手順書へ明記。
- `scripts/verify_public_demo.py` を追加し、root `index.html` と公開URLの UI 必須マーカーを検証できるようにした。
- `.github/workflows/public-demo-guard.yml` を追加し、`main` / `master` への push と PR で root `index.html` の存在・UIマーカーを検証するようにした。
- WBS に `T306` を追加し、公開デモ保護を完了タスクとして記録した。
- Google Sheets の `Mighty-Link WBS` タブへ WBS 15 行を同期済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 6, Updated: 6, Failed: 0`。

公開URLを触る前後の必須コマンド:

```powershell
python scripts/verify_public_demo.py
python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/
```

## 2026-05-21 作業ログ: CATS型WBSスプレッドシート改善

添付参考ファイル `【次期CATS】WBS_分析計画工程(後半).xlsx` を確認し、Google Sheets の WBS 表示を単純一覧から CATS 型の管理表へ改善した。

実施内容:

- `scripts/sync_wbs_to_sheets.py` を拡張し、`data/WBS.tsv` から階層WBS表示を自動生成するようにした。
- `Mighty-Link WBS` タブにタイトル帯、サマリーKPI、フェーズ行、`WBS#` / `Lv` / `WP` / 予定開始日 / 予定終了日 / 予定工数 / 進捗率 / アラート列を追加。
- `WBS Summary` タブを追加し、フェーズ別の総数・完了数・未着手数・完了率・期間を自動集計。
- `WBS Timeline` タブを追加し、タスク別の予定期間・進捗率を横断確認できるようにした。
- 固定ヘッダー、フィルタ、結合セル、列幅、行高、ステータス/アラートの条件付き色分けを Google Sheets API の batch update で適用。
- WBS に `T307` を追加し、CATS型WBSスプレッドシート改善を完了タスクとして記録。

同期・検証:

- Google Sheets へ `16 source rows` / `27 hierarchical WBS display rows` を同期済み。
- `Mighty-Link WBS`, `WBS Summary`, `WBS Timeline` の 3 タブ作成・更新を確認済み。
- Google Calendar `Mighty Skill-Bridge 開発計画` へ再同期済み。最終結果は `Success: 6, Updated: 6, Failed: 0`。
- `python -m compileall src scripts` 成功。
- 公開デモガード `python scripts/verify_public_demo.py --url https://kanta13jp1.github.io/mighty-link-ai-connect/` 成功。
