import os
import json
import glob
import datetime
import re

brain_dir = r"C:\Users\kanta\.gemini\antigravity\brain"
sessions = []

def mask_sensitive(text):
    if not isinstance(text, str):
        return text
    # Mask emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_MASKED]', text)
    # Mask secrets/tokens
    text = re.sub(r'(sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9_-]{10,}|eyJ[A-Za-z0-9_-]{20,})', '***TOKEN_MASKED***', text)
    return text

for d in os.listdir(brain_dir):
    full_path = os.path.join(brain_dir, d)
    if not os.path.isdir(full_path) or d == "tempmediaStorage":
        continue
    log_file = os.path.join(full_path, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_file):
        log_file = os.path.join(full_path, ".system_generated", "logs", "transcript_full.jsonl")
    
    if not os.path.exists(log_file):
        mtime = os.path.getmtime(full_path)
        sessions.append({
            "id": d,
            "mtime": mtime,
            "mtime_jst": datetime.datetime.fromtimestamp(mtime, datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S"),
            "has_log": False,
            "steps": 0,
            "first_user_msg": "",
            "last_user_msg": "",
            "last_model_msg": "",
            "last_tool_call": "",
            "summary": "ログなし（ディレクトリのみ）",
            "status": "不明"
        })
        continue

    mtime = os.path.getmtime(log_file)
    first_user_msg = ""
    last_user_msg = ""
    last_model_msg = ""
    last_tool_call = ""
    step_count = 0
    tools_called = []
    
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            step_count += 1
            try:
                data = json.loads(line)
                stype = data.get("type", "")
                content = data.get("content", "")
                
                if stype == "USER_INPUT":
                    if not first_user_msg:
                        first_user_msg = content
                    last_user_msg = content
                elif stype == "PLANNER_RESPONSE" or stype == "MODEL":
                    if content:
                        last_model_msg = content
                    if "tool_calls" in data and data["tool_calls"]:
                        for tc in data["tool_calls"]:
                            tname = tc.get("name") or tc.get("toolAction") or tc.get("toolSummary") or str(tc)
                            tools_called.append(tname)
                            last_tool_call = tname
            except Exception:
                pass

    # Extract role from first user msg
    role = "未定義"
    first_clean = first_user_msg.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
    role_match = re.search(r'あなたは([^\s。]+担当)です', first_clean) or re.search(r'あなたは([^\s。]+)です', first_clean) or re.search(r'担当[：:]\s*([^\s\n]+)', first_clean)
    if role_match:
        role = role_match.group(1)
    elif "フッター" in first_clean:
        role = "Webフッター担当"
    elif "フロントエンド" in first_clean:
        role = "フロントエンド開発方針担当"
    elif "Git Worktree" in first_clean:
        role = "Git Worktree担当"
    elif "教育担当" in first_clean:
        role = "教育担当"
    elif "スキル一覧" in first_clean:
        role = "スキル一覧・評価担当"

    # Status deduction
    status_eval = "進行中"
    last_clean_user = last_user_msg.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
    if not last_user_msg:
        status_eval = "未開始/空"
    elif any(k in last_clean_user.lower() for k in ["直っていません", "エラー", "ng", "request_changes", "失敗", "動かない"]):
        status_eval = "要対応/未解決"
    elif any(k in last_model_msg for k in ["完了しました", "全件 PASS", "合意完了", "PASS (ドリフト0)"]):
        status_eval = "完了/確認待機"
    elif "進めて" in last_clean_user or "実行" in last_clean_user:
        status_eval = "進行中/実行中"

    sessions.append({
        "id": d,
        "role": role,
        "mtime": mtime,
        "mtime_jst": datetime.datetime.fromtimestamp(mtime, datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S"),
        "has_log": True,
        "steps": step_count,
        "first_user_msg": mask_sensitive(first_clean[:300]),
        "last_user_msg": mask_sensitive(last_clean_user[:300]),
        "last_model_msg": mask_sensitive(last_model_msg[:300]),
        "last_tool_call": mask_sensitive(str(last_tool_call)[:150]),
        "tools_called_count": len(tools_called),
        "status": status_eval
    })

sessions.sort(key=lambda x: x["mtime"], reverse=True)

with open("exports/session_audit_summary.json", "w", encoding="utf-8") as f:
    json.dump(sessions, f, ensure_ascii=False, indent=2)

print(f"Total sessions parsed: {len(sessions)}")
