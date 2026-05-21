#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty Skill-Bridge: API & Web Server Component
Author: Antigravity 2.0 (AI Agent)

This FastAPI application provides:
1. Static hosting for index.html.
2. Dynamic Multimodal AI parsing of resumes & jobs (Gemini 1.5/2.5 Flash).
3. 4-Dimension AI Fit Evaluation.
4. Auto-syncing of matching results to Google Sheets (Mighty Match Logs) with visual decoration.
5. High-quality mock data fallbacks when GEMINI_API_KEY is not configured, ensuring robust demo delivery.
"""

import os
import sys
import datetime
import json
import io
import requests

# Set console encoding to UTF-8 to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Try loading optional libraries for Sheets & Gemini
try:
    import gspread
    from google.oauth2.service_account import Credentials as ServiceCredentials
    from google.oauth2.credentials import Credentials as UserCredentials
    import google.auth.transport.requests
    SHEETS_LIB_AVAILABLE = True
except ImportError:
    SHEETS_LIB_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_LIB_AVAILABLE = True
except ImportError:
    GEMINI_LIB_AVAILABLE = False

# Initialize FastAPI App
app = FastAPI(title="Mighty Skill-Bridge API Server")

# Dynamic Path Resolution (ensures app.py works robustly inside src/)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is src/
PROJECT_ROOT = os.path.dirname(ROOT_DIR)             # Project root

CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")
CLIENT_SECRET_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
SPREADSHEET_ID = "1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8"
USER_EMAIL = "k-umezawa@ml-mightylink.com"

# Mighty-Link Color Palette (Normalized for Sheets API)
COLORS = {
    "header_bg": {"red": 26/255, "green": 115/255, "blue": 232/255},   # #1A73E8 (Mighty Blue)
    "header_text": {"red": 1.0, "green": 1.0, "blue": 1.0},            # White
    "accent_green": {"red": 52/255, "green": 168/255, "blue": 83/255},  # #34A853 (Mighty Green)
    "row_even": {"red": 248/255, "green": 250/255, "blue": 252/255},    # Slate 50
    "border_gray": {"red": 226/255, "green": 232/255, "blue": 240/255}  # Slate 200
}

# Dynamic Environment Diagnostics
API_KEY = os.environ.get("GEMINI_API_KEY")
AI_FORCE_MOCK = os.environ.get("AI_FORCE_MOCK", "").lower() in {"1", "true", "yes", "on"}
GEMINI_READY = API_KEY is not None and GEMINI_LIB_AVAILABLE and not AI_FORCE_MOCK

if GEMINI_READY:
    genai.configure(api_key=API_KEY)
    print("[+] Gemini API successfully configured via GEMINI_API_KEY.")
elif AI_FORCE_MOCK:
    print("[!] AI_FORCE_MOCK enabled. Running in quota-safe mock fallback mode.")
else:
    print("[!] Warning: GEMINI_API_KEY not set or library missing. Running in mock fallback mode.")

# Static Hosting route
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main frontend page index.html."""
    try:
        index_path = os.path.join(ROOT_DIR, "index.html")
        if not os.path.exists(index_path):
            raise FileNotFoundError()
        
        content = None
        # 1. Try reading as strict UTF-8
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
            print("[+] Successfully loaded index.html in strict UTF-8.")
        except UnicodeDecodeError:
            # 2. Try reading as UTF-8, replacing illegal bytes instead of falling back to CP932
            # Since index.html is written in UTF-8, falling back to CP932 causes full text corruption.
            try:
                with open(index_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                print("[!] Loaded index.html in UTF-8 with errors='replace'.")
            except Exception as e:
                # 3. Last resort fallback to CP932
                print(f"[-] UTF-8 fallback failed: {e}. Trying CP932...")
                with open(index_path, "r", encoding="cp932", errors="ignore") as f:
                    content = f.read()
                    
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found in project workspace.")

# API Health Check Endpoint
@app.get("/api/health")
async def health_check():
    """Provides client-side dynamic connection check."""
    return {
        "status": "healthy",
        "sheets_live": SHEETS_LIB_AVAILABLE and (os.path.exists(CREDENTIALS_FILE) or os.path.exists(CLIENT_SECRET_FILE)),
        "gemini_live": GEMINI_READY,
        "ai_mode": "gemini_live" if GEMINI_READY else "mock_fallback",
        "ai_force_mock": AI_FORCE_MOCK
    }

# 1. API: Multi-modal Resume/Job Parser
@app.post("/api/parse")
async def parse_document(
    file: UploadFile = File(None),
    text: str = Form(None),
    doc_type: str = Form("engineer") # "engineer" or "job"
):
    """Parses text or binary files (PDF/Images) and structure them."""
    print(f"[*] API Parse Request received. Type: {doc_type}")
    
    file_bytes = None
    file_name = None
    file_type = None
    
    if file:
        file_bytes = await file.read()
        file_name = file.filename
        file_type = file.content_type
        print(f"  - File uploaded: {file_name} ({file_type}, {len(file_bytes)} bytes)")
    elif text:
        print(f"  - Direct text input received ({len(text)} characters)")
    else:
        raise HTTPException(status_code=400, detail="Either file or text must be provided.")
        
    fallback_reason = "Gemini live mode is not configured."

    # --- Live Gemini Parsing Logic ---
    if GEMINI_READY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = (
                f"You are a professional HR data extraction engine.\n"
                f"Parse the following {doc_type} document and extract a clean structured text summary in Japanese.\n"
                f"Focus on extracting: Name (if engineer), Job Title / Role Name, Core Skills, Cloud / Infra, Databases, and Career Goals.\n"
                f"Make sure to output clean Japanese, keeping important technical details."
            )
            
            response = None
            if file_bytes:
                # Multimodal API Input (PDF/Images)
                pdf_part = {
                    "mime_type": file_type,
                    "data": file_bytes
                }
                response = model.generate_content([prompt, pdf_part])
            else:
                response = model.generate_content(f"{prompt}\n\nDocument Content:\n{text}")
                
            parsed_text = response.text.strip()
            print(f"[+] Gemini Parser Sync completed successfully.")
            return {"status": "success", "ai_mode": "gemini_live", "parsed_content": parsed_text}
            
        except Exception as e:
            fallback_reason = str(e)
            print(f"[-] Gemini live parser failed: {e}. Falling back to high-quality mock parser.")
    elif AI_FORCE_MOCK:
        fallback_reason = "AI_FORCE_MOCK is enabled to avoid Gemini quota usage."

    # --- High-quality Mock Parser Fallback ---
    # To keep the application working beautifully even without an API Key
    import time
    time.sleep(1.0) # Simulating AI processing time
    
    if doc_type == "engineer":
        mock_content = (
            "【氏名】佐藤 賢太 (さとう けんた)\n"
            "【職種】シニアAIソリューションアーキテクト / フルスタックエンジニア\n"
            "【概要】IT業界経験8年。クラウドネイティブなWebアプリケーション開発、特にPython、JavaScript(TypeScript)を用いたAI連携APIの構築実績が豊富。Google Cloud API、OpenAI、Geminiなどの大規模言語モデル(LLM)を活用した自律エージェントの開発や、企業のデータ駆動型意思決定基盤の構築をリード。アジャイル型(Scrum)チームでの開発を得意とし、顧客折衝から要件定義、インフラ設計、実装までエンドエンドで対応可能。\n"
            "【主要スキル】Python, JavaScript, TypeScript, FastAPI, Django, React.js, Next.js, Vertex AI, Gemini API, gspread, SQL\n"
            "【インフラ/データベース】AWS, Google Cloud, PostgreSQL, Pinecone (Vector DB)\n"
            "【キャリア志向】最先端の生成AIを活用したプロダクト開発において、リードエンジニアとしてビジネス価値を創造すること。"
        )
    else:
        mock_content = (
            "【案件名】大手ITソリューション企業：LLM自律エージェント＆データ連携基盤開発\n"
            "【業務内容】生成AI(Gemini, GPT)を活用した業務プロセスの自動化・自律化エージェントの実装、Google API (Sheets API, Docs API) と連携した文書作成自動同期システムの構築、FastAPI / React.js を用いた高パフォーマンスなWebアプリケーションの設計・開発。\n"
            "【必須スキル】Python/TypeScript実務開発（5年以上）、REST API(FastAPI等)設計構築、React.jsまたはNext.js実装実績。\n"
            "【歓迎スキル】Gemini/OpenAI API等のLLM連携実績、Google Cloud API (gspread, Drive API) 等のOAuth認証による連携実績。"
        )
        
    print(f"[+] Mock Parser triggered successfully.")
    return {
        "status": "success",
        "ai_mode": "mock_fallback",
        "fallback_reason": fallback_reason,
        "parsed_content": mock_content
    }


class EvaluationRequest(BaseModel):
    engineer_content: str
    job_content: str

# 2. API: 4-Dimension AI Fit Evaluation
@app.post("/api/match")
async def evaluate_matching(req: EvaluationRequest):
    """Calculates multidimensional matching score and generate interview QA and roadmap."""
    print("[*] API Match Request received.")
    
    fallback_reason = "Gemini live mode is not configured."

    # --- Live Gemini Evaluation Logic ---
    if GEMINI_READY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = (
                "You are the Mighty-Link AI engine. Evaluate the fit between the Candidate Resume and the Job Description.\n"
                "You MUST return the response strictly as a JSON object with the following fields:\n"
                "{\n"
                "  \"final_score\": <Integer from 50 to 100>,\n"
                "  \"scores\": {\n"
                "    \"skill\": <Integer 50-100>,\n"
                "    \"culture\": <Integer 50-100>,\n"
                "    \"growth\": <Integer 50-100>,\n"
                "    \"performing\": <Integer 50-100>\n"
                "  },\n"
                "  \"summary\": \"<Detailed multi-dimensional evaluation summary paragraph in Japanese>\",\n"
                "  \"qa\": [\n"
                "    {\n"
                "      \"question\": \"<Technical interview question tailored for this specific match in Japanese>\",\n"
                "      \"answer\": \"<Best practice guide for candidate answer in Japanese>\",\n"
                "      \"tip\": \"<Tips to enhance points in Japanese>\"\n"
                "    },\n"
                "    {\n"
                "      \"question\": \"<Another relevant interview question in Japanese>\",\n"
                "      \"answer\": \"<Answer guide in Japanese>\",\n"
                "      \"tip\": \"<Tips in Japanese>\"\n"
                "    }\n"
                "  ],\n"
                "  \"roadmap_week1\": \"<Detailed week 1 roadmap actions in Japanese>\",\n"
                "  \"roadmap_week2\": \"<Detailed week 2 roadmap actions in Japanese>\",\n"
                "  \"roadmap_week3\": \"<Detailed week 3 roadmap actions in Japanese>\",\n"
                "  \"roadmap_week4\": \"<Detailed week 4 roadmap actions in Japanese>\"\n"
                "}\n"
                "Do NOT include any markdown code blocks (like ```json) or explanation text outside the JSON.\n\n"
                f"Candidate Resume Data:\n{req.engineer_content}\n\n"
                f"Job Description Data:\n{req.job_content}"
            )
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            res_text = response.text.strip()
            # Clean possible raw markdown block if LLM fails strict config
            if res_text.startswith("```"):
                res_text = res_text.split("\n", 1)[1].rsplit("\n", 1)[0]
                if res_text.startswith("json"):
                    res_text = res_text.split("\n", 1)[1]
            
            match_data = json.loads(res_text.strip())
            match_data["ai_mode"] = "gemini_live"
            print("[+] Gemini Evaluator completed successfully.")
            return match_data
            
        except Exception as e:
            fallback_reason = str(e)
            print(f"[-] Gemini live evaluation failed: {e}. Falling back to high-quality mock evaluator.")
    elif AI_FORCE_MOCK:
        fallback_reason = "AI_FORCE_MOCK is enabled to avoid Gemini quota usage."

    # --- High-quality Mock Evaluation Fallback ---
    import time
    time.sleep(1.5) # Simulating AI processing time
    
    mock_response = {
        "final_score": 89,
        "scores": {
            "skill": 95,
            "culture": 88,
            "growth": 92,
            "performing": 82
        },
        "summary": "本シミュレーターの診断結果、候補者のスキル・経歴は、対象案件（LLM自律エージェント開発）に対して「89%」という極めて高い適合性（Highly Compatible）を示しました。特に「Skill-Fit（95%）」においては、Python、TypeScriptに加え、FastAPIやReactのフルスタックスキル、さらにgspread等を用いたGoogle API連携開発実績が、案件で募集されている技術スタック（FastAPI, React, Sheets/Docs Live 連携）と100%合致しています。また「Growth-Fit（92%）」でも、最先端の生成AIを活用してテクノロジーの架け橋となるアーキテクト像を目指す志向性が、募集背景にあるGemini Spark連携開発の方向性と完全に同期しています。即戦力として、初週からアーキテクチャ設計およびAPI開発で強烈なリーダーシップを発揮できると確信します。",
        "qa": [
            {
                "question": "Google Sheets API や Drive API を活用した、OAuth 2.0 認証を含む連携開発の実績について具体的に教えてください。",
                "answer": "Python (gspread/google-auth) を用いて、サービスアカウントまたはデスクトップ OAuth認証を駆使し、スプレッドシートの自動生成、セル書式設定、429クォータ回避のための batch_update API を実装した経験を具体的に説明します。Windows環境下でのエンコーディングエラー回避など、実践的なトラブルシューティング能力もアピールしてください。",
                "tip": "実際に作成した Python の自動同期スクリプトのモジュール構成や、APIクォータ制限をバッチ処理で劇的に最適化した実績を提示すると非常に好印象です。"
            },
            {
                "question": "生成AI（LLM）と外部システム（RAGやエージェント）を組み合わせる際、どのような設計上の工夫を行ってきましたか？",
                "answer": "単なるAPIコールに留まらず、ローカルデータソースとの整合性を保つためのハイブリッド設計（IndexedDBやSQLite3）や、プロンプトのコンテキストウィンドウを効率化するための構造化パーサー、そしてGeminiのマルチモーダル機能を利用したPDFのパース精度向上に関する工夫を説明します。",
                "tip": "自律エージェントがバックグラウンドタスクとして動き、終了時にユーザーへシームレスに通知する連携シナリオの設計思想をアピールに組み込みましょう。"
            }
        ],
        "roadmap_week1": "既存プラットフォームのAPI仕様書およびGoogle Cloud連携認証フローの把握、ローカル開発環境における client_secret.json などのOAuth認証動作確認、データベース設計（SQLite3/PostgreSQL）の連携モデリング完了",
        "roadmap_week2": "Gemini 3.5 Flash を用いた、バックグラウンドでの自律データ解析エンジンのプロトタイプ作成、gspread を活用した、シートへのバッチ書き込みおよびステータス色付け処理の統合",
        "roadmap_week3": "React.js を用いた、ドラッグ＆ドロップ対応の経歴書アップロードUIの実装、Chart.js による4次元レーダーチャートのレンダリングおよびリアルタイム分析結果描画の統合",
        "roadmap_week4": "Browser Agent による、複数ファイルドロップ時の自律シナリオUIテスト実行、本番公開に向けた CI/CD 環境の設定と、Sheets Live へのデプロイステータス自動通知機能のリリース",
        "ai_mode": "mock_fallback",
        "fallback_reason": fallback_reason
    }
    
    print("[+] Mock Evaluator triggered successfully.")
    return mock_response


class SyncRequest(BaseModel):
    candidate_name: str
    job_name: str
    final_score: int
    skill_score: int
    culture_score: int
    growth_score: int
    performing_score: int
    summary: str

# 3. API: Google Sheets Synchronizer
@app.post("/api/sync")
async def sync_to_sheets(req: SyncRequest):
    """Appends matching evaluation records into Google Sheets with visual formatting."""
    print(f"[*] API Sheets Sync request: {req.candidate_name} <=> {req.job_name}")
    
    if not SHEETS_LIB_AVAILABLE:
        print("[-] gspread library is missing. Cannot perform Sheets Sync.")
        return {"status": "error", "message": "Google Sheets client library is not installed."}
        
    client = None
    auth_mode = None
    
    # 1. OAuth 2.0 Auth Check
    if os.path.exists(CLIENT_SECRET_FILE):
        try:
            client = gspread.oauth(
                credentials_filename=CLIENT_SECRET_FILE,
                authorized_user_filename=AUTHORIZED_USER_FILE
            )
            auth_mode = "OAuth 2.0"
        except Exception as e:
            print(f"[-] OAuth 2.0 authentication failed in API: {e}")

    # 2. Service Account Fallback
    if not client and os.path.exists(CREDENTIALS_FILE):
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = ServiceCredentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            auth_mode = "Service Account"
        except Exception as e:
            print(f"[-] Service Account authentication failed in API: {e}")
            
    if not client:
        print("[-] Authentication credentials not found for Google Sheets.")
        return {"status": "error", "message": "Credentials file not found."}
        
    try:
        # 3. Open Spreadsheet and sheet
        sh = client.open_by_key(SPREADSHEET_ID)
        
        # Check if tab exists, otherwise create it
        tab_name = "Mighty Match Logs"
        try:
            worksheet = sh.worksheet(tab_name)
            print(f"[+] Opened existing sheet: '{tab_name}'")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=tab_name, rows="100", cols="10")
            print(f"[+] Created new sheet: '{tab_name}'")
            
        # Get current data to check headers
        existing_values = worksheet.get_all_values()
        
        headers = ["診断日時", "候補者氏名", "案件・求人名", "総合マッチ度 (%)", "技術 (Skill)", "文化 (Culture)", "キャリア (Growth)", "即戦力 (Performing)", "分析レポート概要"]
        
        # 4. Prepare batch requests list to prevent 429
        requests_list = []
        row_index = 1
        
        if not existing_values:
            # Append headers
            worksheet.append_row(headers)
            existing_values = [headers]
            row_index = 2
        else:
            row_index = len(existing_values) + 1
            
        # Append data row
        jst_now = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
        data_row = [
            jst_now,
            req.candidate_name,
            req.job_name,
            req.final_score,
            req.skill_score,
            req.culture_score,
            req.growth_score,
            req.performing_score,
            req.summary
        ]
        worksheet.append_row(data_row)
        print(f"[+] Successfully appended matching record for {req.candidate_name} into row {row_index}")
        
        # 5. Apply Visual Formatting to Sheets (Mighty Blue Design) via batch update
        sheet_id = worksheet.id
        
        # Gridlines enable
        requests_list.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridlinesVisible": True
                },
                "fields": "gridlinesVisible"
            }
        })
        
        # Format Header Row (Mighty Blue, Bold, White text, Centered)
        requests_list.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": COLORS["header_bg"],
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "foregroundColor": COLORS["header_text"],
                            "bold": True,
                            "fontSize": 11
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat)"
            }
        })
        
        # Format Data Row Just Inserted (Center align scores, gray background if even)
        is_even = row_index % 2 == 0
        cell_format = {
            "verticalAlignment": "MIDDLE",
            "textFormat": {"fontSize": 10}
        }
        if is_even:
            cell_format["backgroundColor"] = COLORS["row_even"]
            
        requests_list.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index - 1,
                    "endRowIndex": row_index,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers)
                },
                "cell": {
                    "userEnteredFormat": cell_format
                },
                "fields": "userEnteredFormat(backgroundColor,verticalAlignment,textFormat)"
            }
        })
        
        # Center align scores specifically (columns index 3 to 7: final_score, skill, culture, growth, performing)
        requests_list.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index - 1,
                    "endRowIndex": row_index,
                    "startColumnIndex": 3,
                    "endColumnIndex": 8
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": COLORS["accent_green"]
                        }
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,textFormat)"
            }
        })
        
        # Auto-resize columns width
        requests_list.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(headers)
                }
            }
        })
        
        # Set specific height for rows
        requests_list.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 0,
                    "endIndex": 1
                },
                "properties": {
                    "pixelSize": 36
                },
                "fields": "pixelSize"
            }
        })
        requests_list.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": row_index - 1,
                    "endIndex": row_index
                },
                "properties": {
                    "pixelSize": 28
                },
                "fields": "pixelSize"
            }
        })
        
        # Execute Visual Formatting Batch Update
        sh.batch_update({"requests": requests_list})
        print(f"[+] Visual styles and formatting applied successfully to '{tab_name}'!")
        
        return {"status": "success", "message": f"Successfully synced matching record into Google Sheets via {auth_mode}."}
        
    except Exception as e:
        print(f"[-] Sheets synchronization failed: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("[*] Starting Mighty Skill-Bridge FastAPI local server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
