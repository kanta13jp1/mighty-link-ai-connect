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
    # Mask potential tokens/keys
    text = re.sub(r'(Bearer\s+|token=|[A-Za-z0-9_-]{20,})', lambda m: m.group(0)[:4] + '***' if len(m.group(0)) > 8 else '***', text)
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
            "last_tool_result": "",
            "summary": "ログなし（ディレクトリのみ）",
            "status": "不明"
        })
        continue

    mtime = os.path.getmtime(log_file)
    first_user_msg = ""
    last_user_msg = ""
    last_model_msg = ""
    last_tool_call = ""
    last_tool_result = ""
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
                elif "tool" in stype.lower() or "result" in stype.lower():
                    last_tool_result = content[:300] if content else ""
            except Exception:
                pass

    # Status deduction
    # Let's inspect last user message vs last model/tool
    status_eval = "進行中"
    if not last_user_msg:
        status_eval = "未開始/空"
    elif any(k in last_user_msg.lower() for k in ["直っていません", "エラー", "ng", "動かない", "修正して", "request_changes", "失敗"]):
        # check if model replied after last user message
        status_eval = "要対応/未解決"
    elif "完了" in last_model_msg or "pass" in last_model_msg.lower() or "合意" in last_model_msg:
        status_eval = "完了/確認待機"

    sessions.append({
        "id": d,
        "mtime": mtime,
        "mtime_jst": datetime.datetime.fromtimestamp(mtime, datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S"),
        "has_log": True,
        "steps": step_count,
        "first_user_msg": mask_sensitive(first_user_msg[:300]),
        "last_user_msg": mask_sensitive(last_user_msg[:300]),
        "last_model_msg": mask_sensitive(last_model_msg[:300]),
        "last_tool_call": mask_sensitive(str(last_tool_call)[:150]),
        "tools_called_count": len(tools_called),
        "status": status_eval
    })

sessions.sort(key=lambda x: x["mtime"], reverse=True)

with open("exports/session_audit_summary.json", "w", encoding="utf-8") as f:
    json.dump(sessions, f, ensure_ascii=False, indent=2)

print(f"Total sessions parsed: {len(sessions)}")
print("\n=== Recent 15 Sessions (JST) ===")
for i, s in enumerate(sessions[:15]):
    print(f"[{i+1}] ID: {s['id']}")
    print(f"    JST: {s['mtime_jst']} | Steps: {s['steps']}")
    print(f"    First User: {s['first_user_msg'][:80]}")
    print(f"    Last User:  {s['last_user_msg'][:80]}")
    print(f"    Last Model: {s['last_model_msg'][:80]}")
    print(f"    Last Tool:  {s['last_tool_call']}")
    print("-" * 60)
