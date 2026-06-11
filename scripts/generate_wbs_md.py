"""Regenerate docs/WBS.md from data/WBS.tsv.

data/WBS.tsv is the WBS source of truth. This script rebuilds the
human-readable docs/WBS.md from it so the two never drift apart.

Usage:
    python scripts/generate_wbs_md.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TSV_PATH = ROOT / "data" / "WBS.tsv"
MD_PATH = ROOT / "docs" / "WBS.md"

HEADER = """# 📊 Mighty-Link AI Connect: プロジェクトWBS (作業分解構成図)

> [!NOTE]
> **本WBSの設計思想**
> 開発するプロダクト **『Mighty Skill-Bridge（エンジニア＆案件 AIフィットシミュレーター）』** を、Antigravity 2.0 およびGoogle Gemini APIの現行モデルを用いて開発するための完全詳細タスクリストです。
> 最新の **Google Workspace API (Sheets/Docs/Calendar) ＆ Gemini API 連携** の思想に基づき、`data/WBS.tsv` を正本として本ファイルは `scripts/generate_wbs_md.py` で自動生成されます。直接編集せず、TSV を更新して再生成してください。

---

## 📅 WBS フェーズ別サマリー

```mermaid
gantt
    title Mighty Skill-Bridge 開発スケジュール
    dateFormat  YYYY-MM-DD
    section フェーズ1: 企画・設計
    要件定義 & DB設計          :done, a1, 2026-05-20, 2d
    section フェーズ2: フロントエンド開発
    UIコンポーネント実装        :done, b1, after a1, 3d
    section フェーズ3: バックエンド & AI
    Gemini API 連携 :done, c1, after b1, 3d
    section フェーズ4: テスト & デバッグ
    Browser Agent & Code Mender :done, d1, after c1, 2d
    section フェーズ5: 本番公開
    CI/CDデプロイ & プレスリリース :done, e1, after d1, 2d
    section フェーズ6: 社長プレゼン準備
    6/2判断材料・デモ・連携フロー準備 :done, f1, 2026-05-21, 13d
    section フェーズ7: 決定後実行
    Firebase/Supabase本番実装・パイロット :active, g1, 2026-06-02, 26d
    section フェーズ8: 本番運用・品質管理
    KPI/SLA・フィードバック・収益化・監査 :active, h1, 2026-06-16, 29d
    section フェーズ9: 長期保守・拡張
    多言語・負荷テスト・モデル追従 : i1, 2026-06-20, 27d
```

---

## 📑 WBS 詳細テーブル

*※正本は `data/WBS.tsv`。スプレッドシートへは `python scripts/sync_wbs_to_sheets.py` で同期します。*

| タスクID | 大フェーズ | 小フェーズ | タスク名 | 担当 | 実行エンジン | Sheets Live 連携アクション | ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""

FOOTER = """
---

## 🤖 Sheets Live & Google Workspace API による自律同期シナリオ

Google Workspace API と `data/WBS.tsv` 正本運用を活かし、このWBSは以下のように同期・稼働します。

1. **リアルタイム進捗更新 (Sheets Live)**
   - 各セッションで `data/WBS.tsv` を更新し、`sync_wbs_to_sheets.py` がGoogle Sheets APIを介してスプレッドシートの該当タスクの進捗ステータスと装飾を更新します。
2. **要件定義書のライブ同期 (Docs Live)**
   - 最初の要件定義（T101）で合意された `requirements.md` の内容は、Google Docs Live に自動で連携され、社長様とリアルタイムで共同編集・コメントのやり取りが可能な状態になります。
3. **24時間自律セキュリティレポート**
   - Code Mender（T402）が脆弱性を検出して自動でコードを修正すると、その安全レポートがスプレッドシート上の「セキュリティ・監査ログ」シートへ自律的に追加され、社長様に毎朝メールでダイジェストが届きます。
4. **完了イベントのカレンダー自動削除**
   - `sync_wbs_to_calendar.py` が `data/WBS.tsv` のステータスを読み、完了済みWBSタスクに対応するGoogle Calendarイベントを削除して、カレンダーを未完了アクションのビューとして維持します。
"""


def escape_cell(value: str) -> str:
    return value.strip().replace("|", "\\|")


def main() -> None:
    rows = []
    with TSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader)
        for row in reader:
            if not row or not row[0].strip():
                continue
            rows.append(row)

    seen_ids = {}
    for row in rows:
        task_id = row[0].strip()
        if task_id in seen_ids:
            raise SystemExit(
                f"Duplicate task ID in {TSV_PATH.name}: {task_id} — fix the TSV first."
            )
        seen_ids[task_id] = row

    lines = [HEADER]
    for row in rows:
        task_id, phase, sub_phase, name, owner, engine, action, status = (
            escape_cell(c) for c in row[:8]
        )
        lines.append(
            f"| **{task_id}** | {phase} | {sub_phase} | {name} | {owner} | {engine} | {action} | {status} |\n"
        )
    lines.append(FOOTER)

    MD_PATH.write_text("".join(lines), encoding="utf-8", newline="\n")
    print(f"[*] Wrote {MD_PATH.relative_to(ROOT)} ({len(rows)} tasks)")


if __name__ == "__main__":
    main()
