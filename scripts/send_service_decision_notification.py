#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate and sync the Service Direction Decision Notification.

This script compiles the formal decision notification decided by the CEO
on 2026-06-02 (Option A: AI Fit Assessment), saves it locally, and automatically
uploads it to Google Drive as a native Google Doc under k-umezawa@ml-mightylink.com.
It also outputs a Slack-ready announcement to the console.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from upload_notebooklm_docs_to_drive import (
    EXPECTED_GOOGLE_ACCOUNT,
    get_file,
    load_credentials,
    upload_as_google_doc,
    verify_workspace_owner,
)


def compile_notification() -> str:
    notification_content = """# 【通知】Mighty Skill-Bridge：6月2日社長報告会におけるサービス方向性の決定について

配信日: 2026年6月2日
送信者: 寛太梅澤 (PM/AI Lead)
対象メンバー: 開発・運用関係者 各位
共有範囲: 社内関係者外秘 (NDA適用)

---

## 📢 決定事項のサマリ

2026年6月2日 15:00-16:00 に開催された第1回 社長報告会（Meet & Gemini 実績）において、小林雅水社長とPM・開発チーム間で合意の上、本プロジェクトの今後のサービス開発方向性が以下の通り決定しました。

* **決定された方向性**: **「方向性 A：AIフィット診断支援」**
* **コア機能**:
  * 従業員・採用候補者向けの適性・状況診断ツール（Gemini APIを用いた適性判定）。
  * 既存の勤怠管理システムと連携した、勤務表データの自動解析および手入力削減。

---

## 🛠️ フェーズ7（決定後実行）の開発ロードマップ

方向性 A の採択に伴い、プロダクションリリースに向けたシステムライフサイクルタスク（WBS Phase 7）を新規追加・編成しました。
6月16日の本番リリースに向けて、以下のロードマップで開発・テスト・インフラ構築を推進します。

1. **インフラ設計・選定 (6/3 〜 6/5)**
   * ホスティング先（お名前.com/GitHub Pages/クラウド）およびDBインフラの最終選定調査（`T730`）。
   * 外部APIシークレット管理およびBasic Authによるセキュリティ環境構築（`T732`）。
2. **バックエンド＆AI実装 (6/5 〜 6/12)**
   * AI適性状況診断および勤務表自動解析バックエンドAPIの本格実装（`T731`）。
3. **品質検証＆CI/CD自動化 (6/8 〜 6/13)**
   * GitHub Actionsを用いた自動ビルド・テスト・デプロイCI/CDパイプライン構築（`T734`）。
   * Playwright等によるUI自動テストおよびAPI単体テストの実装・実行（`T733`）。
4. **本番デプロイ＆リリース (6/13 〜 6/15)**
   * 本番環境への初版デプロイおよび受入手動テスト実施（`T735`）。
5. **運用保守＆APIコスト監視 (6/13 〜 6/16)**
   * API利用メーター監視、日次コスト台帳監査、および超過自動遮断機能の運用適用（`T736`）。

---

## 💡 チームへのお願い・開発体制について

小林雅水社長との合意に基づき、本プロジェクトは**「休日を除く1日1時間程度を目安とする持続可能なAIレバレッジ開発」**で進めます。
人間が泥臭いラインコードを手書きするのではなく、AIエージェント（Codex、Antigravity、Claude Code）の自動生成コードをレビュー・承認・検証するフローを取ることで、1日1時間という限られた人間の時間でプロダクション品質を達成します。

ご不明な点や追加のご質問がございましたら、スプレッドシートの「QA表」タブまたは Slack の進捗確認用スレッドにてご連絡ください。
"""
    return notification_content


def compile_slack_post() -> str:
    slack_post = """
============================================================
📢 Slack/Notion 投稿文案（コピー用）
============================================================
【通知：サービス開発方向性の決定とロードマップ共有】
本日6/2の社長報告会において、Mighty Skill-Bridgeの今後の開発方針が決定しました！

■ 決定されたサービス方向性
👉 「方向性 A：AIフィット診断支援」
（従業員・採用候補者向けの適性診断 ＆ 勤務表の自動パース解析連携）

■ リリースまでの主要マイルストーン
- 6/3 〜 6/5：インフラ・ホスティング設計およびセキュリティ認証層構築
- 6/5 〜 6/12：診断判定ロジック・勤務表パースAPIの本格実装
- 6/8 〜 6/13：Playwright UIテスト・GitHub Actions CI/CD構築
- 6/15：本番デプロイ ＆ 社長受入テスト
- 6/16：APIコスト上限メーター有効化 ＆ 正式リリース予定

■ 開発方針・ルール
- 休日を除く「1日1時間」の人間レビュー体制（AI駆動による並行自動開発）で持続可能に推進します。
- 詳細は Google Drive の通知書、または WBS 管理表をご確認ください。

通知ドキュメントURL: {doc_url}
============================================================
"""
    return slack_post


def main() -> None:
    print("[*] Mighty-Link AI Connect: Generating Service Decision Notification...")
    notification_md = compile_notification()
    
    # Save locally
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    local_path = REPORTS_DIR / "service_decision_notification_2026-06-02.md"
    local_path.write_text(notification_md, encoding="utf-8")
    print(f"[+] Saved local notification draft to: {local_path}")
    
    # Upload to Google Drive
    print("[*] Uploading notification to Google Drive...")
    try:
        credentials = load_credentials()
        title = "Mighty Skill-Bridge Service Direction Decision Notification"
        
        # Save info in reports manifest
        manifest_file = REPORTS_DIR / "reports_manifest.json"
        manifest = {}
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            
        previous_id = manifest.get("service_decision_notification", {}).get("id")
        existing = get_file(credentials, previous_id) if previous_id else None
        existing_id = existing["id"] if existing else None
        
        result = upload_as_google_doc(
            credentials,
            title=title,
            content=notification_md,
            existing_file_id=existing_id,
        )
        verify_workspace_owner(result)
        
        url = result.get("webViewLink") or f"https://docs.google.com/document/d/{result['id']}/edit"
        manifest["service_decision_notification"] = {
            "id": result["id"],
            "name": result["name"],
            "url": url,
            "updated_at": result.get("modifiedTime") or ""
        }
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        
        print(f"[+] Service Decision Notification successfully uploaded to Google Drive!")
        print(f"[*] Google Doc URL: {url}")
        
        # Safely encode stdout for Windows CP932 terminal environments
        encoding = sys.stdout.encoding or 'utf-8'
        raw_post = compile_slack_post().format(doc_url=url)
        safe_post = raw_post.encode(encoding, errors='replace').decode(encoding)
        print(safe_post)
        
    except Exception as exc:
        print(f"[-] Google Drive upload failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
