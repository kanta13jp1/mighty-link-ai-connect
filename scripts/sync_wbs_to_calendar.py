#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: WBS Google Calendar Sync Script
Author: Antigravity 2.0 (AI Agent)

This script:
1. Generates an 'exports/mighty_development_plan.ics' file for offline import.
2. Synchronizes WBS milestones and the CEO meeting to Google Calendar using:
   - OAuth 2.0 (via client_secret.json) -> Creates a custom "Mighty Skill-Bridge 開発計画" calendar on user's drive.
   - Service Account (via credentials.json) -> Falls back to writing directly to user's calendar or sharing events.
"""

import os
import sys
import csv
import datetime
import uuid
import json
import hashlib
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "exports")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def install_and_import(package):
    """Dynamically checks and instructs how to install dependencies if missing."""
    try:
        __import__(package)
    except ImportError:
        print(f"[-] Required library '{package}' is not installed.")
        print(f"[*] Please install it by running: pip install -r requirements.txt")
        sys.exit(1)

# Ensure dependencies are available
install_and_import("gspread")
install_and_import("google.oauth2")

import gspread
from google.oauth2.service_account import Credentials
import google.auth.transport.requests
from google_workspace_account import (
    GoogleWorkspaceAccountError,
    assert_expected_google_account,
    credentials_from_gspread_client,
)

# Configuration
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")       # Service Account
CLIENT_SECRET_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")   # OAuth 2.0 Desktop client
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
USER_EMAIL = "k-umezawa@ml-mightylink.com"
WBS_FILE = os.path.join(PROJECT_ROOT, "data", "WBS.tsv")

# WBS Schedule definitions (Parsed from docs/WBS.md / data/WBS.tsv)
SCHEDULE_EVENTS = [
    {
        "summary": "【Mighty Skill-Bridge】フェーズ1: 企画・設計（要件定義 & DB設計）",
        "description": "開発の土台となる要件定義(requirements.md)およびDB設計(database.md)の策定・合意。",
        "start_date": "2026-05-20",
        "end_date": "2026-05-22", # 2 days (exclusive end date is 22nd)
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ2: フロント開発（UI/UX実装）",
        "description": "プレミアムなガラスモフィズム調UI、ドラッグ＆ドロップパネル、Chart.js連携の実装。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-25", # 3 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ3: バックエンド & AI（Gemini API連携）",
        "description": "FastAPIを用いたマルチモーダルパースAPI、4次元分析API、Google Sheets同期エンジン、構造化プロファイル抽出・4軸スコアリングfallback基盤、AI判定監査ログ(JSONL)・recent audit API、GitHub Pages公開デモ保護ガード、CATS型WBSスプレッドシートUIの開発。",
        "start_date": "2026-05-25",
        "end_date": "2026-05-28", # 3 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ4: テスト & デバッグ（Browser Agent & Code Mender）",
        "description": "Browser Agentによる自律UIテスト、Code Menderによるセキュリティ診断・デバッグ。",
        "start_date": "2026-05-28",
        "end_date": "2026-05-30", # 2 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ5: 本番公開（CI/CDデプロイ & プレスリリース）",
        "description": "GitHub ActionsによるCI/CD環境構築、リリース、およびプレスリリース告知文の自動生成・公開。",
        "start_date": "2026-05-30",
        "end_date": "2026-06-01", # 2 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ6: 社長プレゼン準備（6/2判断材料・デモ・想定QA）",
        "description": "6/2の社長打ち合わせに向け、サービス内容を決め打ちせず、公開デモ、WBS、Google Workspace連携、論点、選択肢、判断マトリクス、議事録テンプレート、想定QA、決定後の反映手順を準備します。",
        "start_date": "2026-05-21",
        "end_date": "2026-06-02",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】社長プレゼン判断材料レビュー",
        "description": "スライド構成、判断マトリクス、想定質問、デモバックアップ導線を確認し、6/2で決める事項と保留事項を分離します。",
        "start_time": "2026-05-30T10:00:00",
        "end_time": "2026-05-30T11:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】社長向け事前共有メモ作成",
        "description": "社長へ事前共有する確認ポイント、当日アジェンダ、公開デモURL、WBS/Calendar確認導線の短文ドラフトを作成します。",
        "start_date": "2026-05-30",
        "end_date": "2026-06-01",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】開発ナレッジ連携フロー整理",
        "description": "NotebookLM、Slack、Notion、Obsidianを6/2の社長判断材料として整理し、正式実装前に役割・情報管理・導入優先順位を確認します。",
        "start_date": "2026-05-24",
        "end_date": "2026-05-29",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】連携ツール採用判断レビュー",
        "description": "NotebookLM/Slack/Notion/Obsidianの採用・保留・後回し、共有範囲、権限ルール、6/2以降の実装候補をレビューします。",
        "start_time": "2026-05-28T14:00:00",
        "end_time": "2026-05-28T15:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】開発ナレッジ連携デモ確認",
        "description": "NotebookLM投入資料、Slack投稿案、Notion CSV、Obsidian vault、公開デモUI、FastAPI生成APIを確認し、社長に見せる順番を固めます。",
        "start_time": "2026-05-29T15:00:00",
        "end_time": "2026-05-29T16:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】CLI/MCP連携証跡レビュー",
        "description": "GitHub Issues、Google Docs化したNotebookLM source pack、Notion証跡ページ、Obsidian vault、Slack投稿案、GitHub Project権限課題を確認し、6/2で見せる順番を決めます。",
        "start_time": "2026-05-23T11:00:00",
        "end_time": "2026-05-23T12:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】GitHub Project権限復旧チェック",
        "description": "gh auth refresh -s read:project 実行後にProject board取得/作成とIssue #1-#11/#13/#14/#16の配置可否を確認します。",
        "start_time": "2026-05-24T10:00:00",
        "end_time": "2026-05-24T11:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLMプレゼン草案作成",
        "description": "NotebookLMへSource PackとPresentation Briefを投入し、6/2社長説明用の8枚以内スライド構成、話す要点、想定QAを生成します。",
        "start_time": "2026-05-22T15:00:00",
        "end_time": "2026-05-22T16:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】Slack投稿先・送信権限確認",
        "description": "Slack投稿案を実送信するため、投稿先チャンネル、社長共有範囲、Slack connector/CLIの利用可否を確認します。",
        "start_time": "2026-05-24T11:00:00",
        "end_time": "2026-05-24T11:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】Google Workspace OAuthアカウント固定確認",
        "description": "authorized_user.jsonがk-umezawa@ml-mightylink.comに紐づいていることをDrive APIで確認し、Sheets/Calendar/API同期前の誤アカウント防止ガードを追加します。",
        "start_date": "2026-05-21",
        "end_date": "2026-05-22",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】Workspace Google Docs再作成確認",
        "description": "NotebookLM用Source PackとPresentation BriefをLocal OAuth Drive APIでk-umezawa@ml-mightylink.com所有のGoogle Docsとして再作成し、Google Docsホームに表示される状態を確認します。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-23",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】docs NotebookLM同期・Google Docs化",
        "description": "docs/*.md 22件をLocal OAuth Drive APIでk-umezawa@ml-mightylink.com所有のGoogle Docsへ同期し、NotebookLM CLI source add-drive用manifestを作成します。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-23",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM CLI再認証・Source追加",
        "description": "notebooklm_login_workspace.pyでk-umezawa@ml-mightylink.comのCLI認証状態を保存し、sync_docs_to_notebooklm.pyでNotebookLMへdocs sourceを追加します。",
        "start_time": "2026-05-22T13:00:00",
        "end_time": "2026-05-22T13:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM Agent Brief取得",
        "description": "NotebookLM ask/summaryで設計情報・ロードマップ・6/2前タスクを要約し、AIエージェントの次回開発入力としてnotebooklm_agent_brief.mdへ保存します。",
        "start_time": "2026-05-22T13:30:00",
        "end_time": "2026-05-22T14:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM補助ログイン導線作成",
        "description": "upstream notebooklm loginのGoogle Accounts遷移中断に備え、Workspace専用の補助ログインスクリプトを作成し、storage_stateを保存できる状態にします。",
        "start_time": "2026-05-22T12:30:00",
        "end_time": "2026-05-22T13:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM CEO Slide Outline取得",
        "description": "NotebookLMの22 source ready状態から、6/2社長説明用の8枚以内スライド草案、話す要点、想定質問を取得し、Google Docs化対象に追加します。",
        "start_time": "2026-05-22T14:00:00",
        "end_time": "2026-05-22T14:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM PowerPoint化",
        "description": "NotebookLM CLIで取得したCEO Slide Outlineを社長説明用PowerPointへ変換し、exports/knowledge_flow配下にPPTXと生成サマリーを保存します。",
        "start_time": "2026-05-22T16:00:00",
        "end_time": "2026-05-22T17:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】PowerPoint Drive共有・Notion証跡更新",
        "description": "社長説明用PPTXをk-umezawa@ml-mightylink.com所有のGoogle Driveへアップロードし、Notion MCPでNotebookLM/PPTX/Slack/Projectの証跡を更新します。",
        "start_time": "2026-05-22T17:00:00",
        "end_time": "2026-05-22T18:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】三ツール開発フロー整備",
        "description": "Antigravity + Gemini、VSCode + Codex、VSCode + Claude Codeを併用する開発ゲート、公式Docs確認、Sheets課題管理表・QA表同期、commit/push/main/master反映の手順を固定します。",
        "start_time": "2026-05-22T18:00:00",
        "end_time": "2026-05-22T18:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】古いドキュメント削除・最新化",
        "description": "公式Docs確認後、未確認の未来モデル前提、古いNotebookLM件数、古いIssue番号を削除または現在形へ置き換えます。",
        "start_time": "2026-05-22T19:00:00",
        "end_time": "2026-05-22T19:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】GitHub Issues/Project再追跡",
        "description": "PowerPoint生成Issueを追加し、GitHub Projectはread:project/projectスコープ不足としてIssue #8/#5で復旧待ちを継続します。",
        "start_time": "2026-05-24T13:00:00",
        "end_time": "2026-05-24T14:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】6/2資料最終パックレビュー",
        "description": "PPTX、NotebookLM資料、WBS、Calendar、GitHub Issues、Notion証跡、Slack投稿案を通しで確認し、社長に見せる順番を固定します。",
        "start_time": "2026-05-30T16:00:00",
        "end_time": "2026-05-30T17:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】社長プレゼン最終リハーサル",
        "description": "公開URL、ローカルAPI、Google Sheets WBS、Calendar同期、説明資料、想定QA、バックアップ手順を最終確認します。",
        "start_time": "2026-06-01T16:00:00",
        "end_time": "2026-06-01T17:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】第1回 社長報告会（プロジェクト方針決定）",
        "description": "「Mighty Skill-Bridge」の公開デモ、WBS、Google Workspace連携、6/2以降の企画・サービス内容・優先機能・開発方針を確認し、決定します。",
        "start_time": "2026-06-02T13:00:00",
        "end_time": "2026-06-02T14:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】requirements.txt 依存ドリフトの監視・freeze",
        "description": "dependencyのfreezeとupgrade禁止期間の運用監視。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-24",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: 個人情報同意書テンプレート作成と運用設計",
        "description": "社長承認後の同意書テンプレート整備と運用ルールの策定。",
        "start_date": "2026-06-03",
        "end_date": "2026-06-06",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: デモ環境アクセス制限(basic auth/IP制限)導入設計",
        "description": "社長承認後のデモ環境認証/アクセス制限実装。",
        "start_date": "2026-06-06",
        "end_date": "2026-06-09",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: 3 AIツール並走quotaメーター監視設計",
        "description": "社長承認後のコスト上限設定および優先laneポリシー決定。",
        "start_date": "2026-06-09",
        "end_date": "2026-06-11",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】Antigravity 2.0 Managed Agents料金・利用条件確認",
        "description": "公式情報に基づくManaged Agents料金監視体制の整備。",
        "start_date": "2026-05-24",
        "end_date": "2026-05-26",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: 3-tool体制開発手順書による属人性軽減と再現性確保",
        "description": "マルチAIワークフロー手順書の継続更新と属人性排除。",
        "start_date": "2026-05-22",
        "end_date": "2026-06-03",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】Codexセッション設定リポジトリレベル固定化",
        "description": "設定ファイルの適用によるセッションドリフト防止。",
        "start_date": "2026-05-26",
        "end_date": "2026-05-28",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: NotebookLM同期スクリプトGemini context caching導入検証",
        "description": "Google公式caching docsに沿ったTTL指定によるコスト削減PoC。",
        "start_date": "2026-06-11",
        "end_date": "2026-06-12",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: Codex skills定型運用コマンドパッケージ化",
        "description": "1 job = 1 skill 規則に従った自動化パッケージ整備。",
        "start_date": "2026-06-12",
        "end_date": "2026-06-13",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】Antigravity CLI機能評価と動作検証",
        "description": "Google公式Docsに基づくCLI実機検証と可否判断。",
        "start_date": "2026-05-28",
        "end_date": "2026-05-29",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】主要docs内markdownlint指摘事項一括自動修正",
        "description": "markdownlint --fixによる構造不整合の一括解消。",
        "start_date": "2026-05-29",
        "end_date": "2026-05-30",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: Antigravity hooks自動起動可否検証",
        "description": "自動化トリガーのPoCとマルチAI自動同期パイプライン整備。",
        "start_date": "2026-06-13",
        "end_date": "2026-06-14",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: Canvaインポート用PPTXミニマルスタイル追加",
        "description": "--style canva-exportオプションによるCanva向け平滑PPTX生成。",
        "start_date": "2026-06-14",
        "end_date": "2026-06-16",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ7: Playwrightによるデモ画面スクショ自動取得スクリプト実装",
        "description": "複数画面の定期自動キャプチャによるスライド素材作成自動化。",
        "start_date": "2026-06-16",
        "end_date": "2026-06-18",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】Figma MCPを用いたワイヤーフレーム自動流し込み",
        "description": "Figma API/MCP連携によるワイヤーフレームフレーム一括構築。",
        "start_date": "2026-05-30",
        "end_date": "2026-05-31",
        "is_all_day": True
    }
]

STALE_EVENT_SUMMARIES = [
    "【Mighty Skill-Bridge】フェーズ3: バックエンド & AI（Gemini 3.5 & Omni 連携API）",
]

# Calendar events can represent one or more WBS rows. Completed rows should be
# removed from Google Calendar so the remaining calendar is an action view.
EVENT_WBS_IDS_BY_INDEX = {
    0: ["T101", "T102"],
    1: ["T201", "T202"],
    2: ["T301", "T302", "T303", "T304", "T305", "T306", "T307"],
    3: ["T401", "T402"],
    4: ["T501", "T502"],
    7: ["T614"],
    8: ["T616"],
    11: ["T638"],
    15: ["T647"],
    16: ["T648"],
    17: ["T649"],
    18: ["T650"],
    19: ["T651"],
    20: ["T656"],
    21: ["T657"],
    22: ["T658"],
    23: ["T659", "T660"],
    24: ["T664"],
    25: ["T665"],
    26: ["T684"],
    27: ["T685"],
    28: ["T686"],
    29: ["T687"],
    30: ["T688"],
    31: ["T689"],
    32: ["T690"],
    33: ["T691"],
    34: ["T692"],
    35: ["T693"],
    36: ["T694"],
    37: ["T695"],
    38: ["T696"],
    39: ["T697"],
    40: ["T698"],
}

COMPLETED_STATUS = "完了"


def load_wbs_statuses():
    """Loads WBS status by task id from the local source of truth."""
    if not os.path.exists(WBS_FILE):
        print(f"[!] WBS source not found. Calendar sync will keep all events: {WBS_FILE}")
        return {}

    with open(WBS_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return {
            row.get("タスクID", "").strip(): row.get("ステータス", "").strip()
            for row in reader
            if row.get("タスクID")
        }


def event_wbs_ids(event_index):
    """Returns WBS ids represented by a schedule event index."""
    return EVENT_WBS_IDS_BY_INDEX.get(event_index, [])


def is_event_completed(event_index, wbs_statuses):
    """True when every mapped WBS row for this event is complete."""
    ids = event_wbs_ids(event_index)
    return bool(ids) and all(wbs_statuses.get(task_id) == COMPLETED_STATUS for task_id in ids)


def iter_events_for_sync(wbs_statuses):
    """Yields events that should remain visible in Calendar/ICS."""
    for index, ev in enumerate(SCHEDULE_EVENTS):
        if is_event_completed(index, wbs_statuses):
            continue
        yield index, ev


def iter_completed_events(wbs_statuses):
    """Yields events that should be deleted from Google Calendar."""
    for index, ev in enumerate(SCHEDULE_EVENTS):
        if is_event_completed(index, wbs_statuses):
            yield index, ev


def generate_ics_file(wbs_statuses=None):
    """Generates standard iCalendar (.ics) file for 1-click import."""
    print("[*] Generating iCalendar (.ics) file...")
    wbs_statuses = wbs_statuses or load_wbs_statuses()
    sync_events = list(iter_events_for_sync(wbs_statuses))
    skipped_count = len(SCHEDULE_EVENTS) - len(sync_events)
    
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mighty-Link//AI Connect Calendar Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mighty Skill-Bridge 開発計画",
        "X-WR-TIMEZONE:Asia/Tokyo"
    ]
    
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    for _index, ev in sync_events:
        ics_lines.append("BEGIN:VEVENT")
        stable_uid = uuid.uuid5(uuid.NAMESPACE_URL, ev["summary"])
        ics_lines.append(f"UID:{stable_uid}@mighty-link.ai")
        ics_lines.append(f"DTSTAMP:{now_str}")
        ics_lines.append(f"SUMMARY:{ev['summary']}")
        ics_lines.append(f"DESCRIPTION:{ev['description']}")
        
        if ev["is_all_day"]:
            start = ev["start_date"].replace("-", "")
            end = ev["end_date"].replace("-", "")
            ics_lines.append(f"DTSTART;VALUE=DATE:{start}")
            ics_lines.append(f"DTEND;VALUE=DATE:{end}")
        else:
            # Format: 2026-06-02T13:00:00 -> 20260602T130000
            start = ev["start_time"].replace("-", "").replace(":", "")
            end = ev["end_time"].replace("-", "").replace(":", "")
            ics_lines.append(f"DTSTART;TZID=Asia/Tokyo:{start}")
            ics_lines.append(f"DTEND;TZID=Asia/Tokyo:{end}")
            
        ics_lines.append("END:VEVENT")
        
    ics_lines.append("END:VCALENDAR")
    
    ics_content = "\r\n".join(ics_lines) + "\r\n"
    
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    filepath = os.path.join(EXPORTS_DIR, "mighty_development_plan.ics")
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(ics_content)
        
    print(f"[+] iCalendar (.ics) file generated successfully: {os.path.abspath(filepath)}")
    print(f"[*] Active events exported: {len(sync_events)}; completed events skipped: {skipped_count}")
    print("[*] You can import this file directly into Google Calendar, Outlook, or Apple Calendar.")
    return filepath

from google.oauth2.credentials import Credentials as UserCredentials

def get_google_auth_token(auth_mode):
    """Retrieves standard Access Token directly from JSON files depending on auth_mode."""
    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
    if "OAuth" in auth_mode:
        if os.path.exists(AUTHORIZED_USER_FILE):
            with open(AUTHORIZED_USER_FILE, "r", encoding="utf-8") as f:
                info = json.load(f)
            creds = UserCredentials.from_authorized_user_info(info)
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            return creds.token
    elif "Service Account" in auth_mode:
        if os.path.exists(CREDENTIALS_FILE):
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            return creds.token
    raise Exception("No valid credentials found to extract access token.")

def build_event_body(ev, wbs_ids=None):
    """Builds a deterministic Calendar API event payload."""
    private_props = {
        "syncSource": "mighty-link-ai-connect",
        "syncKey": hashlib.sha1(ev["summary"].encode("utf-8")).hexdigest()
    }
    if wbs_ids:
        private_props["wbsIds"] = ",".join(wbs_ids)

    event_body = {
        "summary": ev["summary"],
        "description": ev["description"],
        "extendedProperties": {
            "private": private_props
        }
    }

    if ev["is_all_day"]:
        event_body["start"] = {"date": ev["start_date"]}
        event_body["end"] = {"date": ev["end_date"]}
    else:
        event_body["start"] = {"dateTime": ev["start_time"], "timeZone": ev["time_zone"]}
        event_body["end"] = {"dateTime": ev["end_time"], "timeZone": ev["time_zone"]}

    return event_body

def event_window_params(ev):
    """Returns a small search window for finding existing calendar events."""
    if ev["is_all_day"]:
        start = datetime.date.fromisoformat(ev["start_date"]) - datetime.timedelta(days=1)
        end = datetime.date.fromisoformat(ev["end_date"]) + datetime.timedelta(days=1)
        return {
            "timeMin": f"{start.isoformat()}T00:00:00+09:00",
            "timeMax": f"{end.isoformat()}T23:59:59+09:00"
        }

    start_dt = datetime.datetime.fromisoformat(ev["start_time"]) - datetime.timedelta(hours=6)
    end_dt = datetime.datetime.fromisoformat(ev["end_time"]) + datetime.timedelta(hours=6)
    return {
        "timeMin": f"{start_dt.isoformat()}+09:00",
        "timeMax": f"{end_dt.isoformat()}+09:00"
    }

def event_matches(existing_event, desired_event):
    """Checks summary and start/end values so re-sync updates instead of duplicating."""
    if existing_event.get("summary") != desired_event.get("summary"):
        return False
    existing_start = existing_event.get("start", {})
    existing_end = existing_event.get("end", {})
    desired_start = desired_event.get("start", {})
    desired_end = desired_event.get("end", {})
    return event_time_value(existing_start) == event_time_value(desired_start) and event_time_value(existing_end) == event_time_value(desired_end)

def event_time_value(event_time):
    if "date" in event_time:
        return event_time["date"]
    # Google may return 2026-06-02T13:00:00+09:00 while the request uses
    # dateTime plus a timeZone field. Compare the local timestamp portion.
    return event_time.get("dateTime", "")[:19]

def find_existing_event(headers, calendar_id, ev, desired_event):
    list_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    params = {
        "q": ev["summary"],
        "singleEvents": "true",
        "orderBy": "startTime",
        "timeMin": "2026-05-19T00:00:00+09:00",
        "timeMax": "2026-06-25T23:59:59+09:00"
    }
    res = requests.get(list_url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"  [!] Could not check existing events for {ev['summary']}: {res.text}")
        return None

    desired_key = desired_event.get("extendedProperties", {}).get("private", {}).get("syncKey")
    matches = []
    for item in res.json().get("items", []):
        private_props = item.get("extendedProperties", {}).get("private", {})
        same_summary = item.get("summary") == desired_event.get("summary")
        same_key = desired_key and private_props.get("syncKey") == desired_key
        if same_summary or same_key:
            matches.append(item)

    if not matches:
        return None

    exact_matches = [item for item in matches if event_matches(item, desired_event)]
    selected = exact_matches[0] if exact_matches else matches[0]

    for duplicate in matches:
        if duplicate.get("id") != selected.get("id"):
            delete_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{duplicate['id']}"
            delete_res = requests.delete(delete_url, headers=headers)
            if delete_res.status_code in [200, 204]:
                print(f"  [*] Removed duplicate event: {ev['summary']}")
            else:
                print(f"  [!] Failed to remove duplicate event {duplicate['id']}: {delete_res.text}")

    return selected

def remove_events_by_summary(headers, calendar_id, summaries, reason):
    """Deletes matching calendar events in the project window."""
    list_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    deleted_count = 0
    for summary in summaries:
        params = {
            "q": summary,
            "singleEvents": "true",
            "timeMin": "2026-05-19T00:00:00+09:00",
            "timeMax": "2026-06-25T23:59:59+09:00",
        }
        res = requests.get(list_url, headers=headers, params=params)
        if res.status_code != 200:
            print(f"  [!] Could not check {reason} events for {summary}: {res.text}")
            continue
        for item in res.json().get("items", []):
            if item.get("summary") != summary:
                continue
            delete_url = f"{list_url}/{item['id']}"
            delete_res = requests.delete(delete_url, headers=headers)
            if delete_res.status_code in [200, 204]:
                print(f"  [*] Removed {reason} event: {summary}")
                deleted_count += 1
            else:
                print(f"  [!] Failed to remove {reason} event {item['id']}: {delete_res.text}")
    return deleted_count


def remove_stale_event_aliases(headers, calendar_id):
    """Deletes known stale event titles so renamed WBS events do not linger."""
    return remove_events_by_summary(headers, calendar_id, STALE_EVENT_SUMMARIES, "stale")


def remove_completed_wbs_events(headers, calendar_id, wbs_statuses):
    """Deletes Calendar events whose mapped WBS tasks are complete."""
    completed_events = list(iter_completed_events(wbs_statuses))
    completed_summaries = [ev["summary"] for _index, ev in completed_events]
    if not completed_summaries:
        print("[*] No completed WBS-linked calendar events to remove.")
        return 0

    print(f"[*] Removing completed WBS-linked calendar events: {len(completed_summaries)} target title(s)")
    return remove_events_by_summary(headers, calendar_id, completed_summaries, "completed WBS")


def sync_to_google_calendar(access_token, auth_mode, wbs_statuses):
    """Creates events in Google Calendar via HTTP REST API."""
    print(f"[*] Starting API Sync (Auth Mode: {auth_mode})...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 1. Determine which Calendar to write to
    target_calendar_id = "primary"
    
    # If OAuth 2.0 (User Drive), we can list and create custom calendars!
    if "OAuth" in auth_mode:
        print("[*] Checking for existing custom 'Mighty Skill-Bridge 開発計画' calendar...")
        list_url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
        res = requests.get(list_url, headers=headers)
        
        if res.status_code == 200:
            calendars = res.json().get("items", [])
            for cal in calendars:
                if cal.get("summary") == "Mighty Skill-Bridge 開発計画":
                    target_calendar_id = cal.get("id")
                    print(f"[+] Found existing custom calendar. ID: {target_calendar_id}")
                    break
            
            if target_calendar_id == "primary":
                print("[*] Custom calendar not found. Creating a new one...")
                create_url = "https://www.googleapis.com/calendar/v3/calendars"
                cal_body = {"summary": "Mighty Skill-Bridge 開発計画", "timeZone": "Asia/Tokyo"}
                c_res = requests.post(create_url, headers=headers, json=cal_body)
                
                if c_res.status_code == 200:
                    target_calendar_id = c_res.json().get("id")
                    print(f"[+] Successfully created new custom calendar! ID: {target_calendar_id}")
                else:
                    print(f"[-] Failed to create custom calendar ({c_res.status_code}). Using Primary calendar instead.")
        else:
            print(f"[-] Failed to fetch calendar list. Using Primary calendar.")

    # 2. In Service Account Mode, we attempt to write to USER_EMAIL
    if "Service Account" in auth_mode:
        target_calendar_id = USER_EMAIL
        print(f"[*] Service Account mode: Writing to {USER_EMAIL} (Requires manual calendar sharing configured).")

    stale_deleted_count = remove_stale_event_aliases(headers, target_calendar_id)
    completed_deleted_count = remove_completed_wbs_events(headers, target_calendar_id, wbs_statuses)

    # 3. Create Events
    success_count = 0
    fail_count = 0
    update_count = 0
    sync_events = list(iter_events_for_sync(wbs_statuses))
    
    for event_index, ev in sync_events:
        event_body = build_event_body(ev, event_wbs_ids(event_index))
        existing_event = find_existing_event(headers, target_calendar_id, ev, event_body)

        if existing_event:
            event_url = f"https://www.googleapis.com/calendar/v3/calendars/{target_calendar_id}/events/{existing_event['id']}"
            res = requests.patch(event_url, headers=headers, json=event_body)
            action_label = "Updated"
        else:
            insert_url = f"https://www.googleapis.com/calendar/v3/calendars/{target_calendar_id}/events"
            res = requests.post(insert_url, headers=headers, json=event_body)
            action_label = "Created"
        
        if res.status_code in [200, 201]:
            print(f"  [+] {action_label} event: {ev['summary']}")
            success_count += 1
            if existing_event:
                update_count += 1
        else:
            print(f"  [-] Failed to sync event: {ev['summary']} | Error: {res.text}")
            fail_count += 1
            
    print("="*60)
    print(
        "[+] API Sync Complete! "
        f"Active: {len(sync_events)}, Success: {success_count}, Updated: {update_count}, "
        f"Failed: {fail_count}, Deleted completed: {completed_deleted_count}, Deleted stale: {stale_deleted_count}"
    )
    
    if fail_count > 0 and "Service Account" in auth_mode:
        print("[!] Note: Google Service Accounts cannot write to your calendar by default.")
        print(f"    Please share your calendar with the service account email with 'Make changes' permission,")
        print("    or import the generated 'exports/mighty_development_plan.ics' file.")
    print("="*60)

def main():
    # Configure stdout/stderr encoding to UTF-8 to prevent encoding errors on Windows terminal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    print("="*60)
    print("[*] Mighty-Link AI Connect: WBS Google Calendar Sync Tool")
    print("="*60)

    wbs_statuses = load_wbs_statuses()

    # Always generate the .ics file first (failsafe & convenient)
    generate_ics_file(wbs_statuses)
    
    client = None
    auth_mode = None

    # 1. OAuth 2.0 Desktop Authentication (Priority)
    if os.path.exists(CLIENT_SECRET_FILE):
        print("[*] Found OAuth 2.0 client credentials. Authenticating...")
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events"
            ]
            client = gspread.oauth(
                scopes=scopes,
                credentials_filename=CLIENT_SECRET_FILE,
                authorized_user_filename=AUTHORIZED_USER_FILE
            )
            assert_expected_google_account(credentials_from_gspread_client(client), USER_EMAIL)
            auth_mode = "OAuth 2.0 (User Drive)"
            print("[+] OAuth 2.0 Authentication Successful!")
        except GoogleWorkspaceAccountError as e:
            print(f"[-] OAuth 2.0 Workspace Account Verification Failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[-] OAuth 2.0 Authentication Failed: {e}")
            print("[*] Falling back to Service Account check...")

    # 2. Service Account Fallback
    if not client and os.path.exists(CREDENTIALS_FILE):
        print("[*] Authenticating via Google Cloud Service Account...")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
        try:
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            auth_mode = "Service Account"
            print("[+] Service Account Authentication Successful!")
        except Exception as e:
            print(f"[-] Service Account Authentication Failed: {e}")

    # 3. Perform Sync if Client authenticated
    if client:
        try:
            access_token = get_google_auth_token(auth_mode)
            sync_to_google_calendar(access_token, auth_mode, wbs_statuses)
        except Exception as e:
            print(f"[-] API Execution failed: {e}")
            print("[*] Please import the generated 'exports/mighty_development_plan.ics' file manually.")
    else:
        print("[-] API Authentication credentials not found.")
        print("[*] Synchronized WBS via iCalendar file successfully. Please import the .ics file manually.")

if __name__ == "__main__":
    main()
